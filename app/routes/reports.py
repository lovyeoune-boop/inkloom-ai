from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path
import uuid, shutil
from ..database import get_db
from ..models import User, Report
from ..schemas import ReviewTextIn, ReviewDecisionIn
from ..security import get_current_user, require_reviewer
from ..services.moderation import ModerationProviderError, moderate_text, moderate_media_stub
from ..config import UPLOAD_DIR, MAX_UPLOAD_MB

router = APIRouter(prefix="/api/reports", tags=["Content reports"])
AGE_BANDS = {"under_5", "5_8", "9_12", "13_17"}
MEDIA_TYPES = {"image": {".png", ".jpg", ".jpeg", ".webp"}, "audio": {".mp3", ".wav", ".m4a"}, "video": {".mp4", ".mov", ".webm"}}

def report_out(r, include_content=False):
    report = {
        "id": r.id, "title": r.title, "content_type": r.content_type, "age_band": r.age_band,
        "status": r.status, "recommendation": r.recommendation, "risk_level": r.risk_level,
        "findings": r.findings or [], "created_at": r.created_at.isoformat() if r.created_at else None,
        "reviewer_note": r.reviewer_note
    }
    if include_content:
        report["content_text"] = r.content_text
    return report

@router.post("/text")
def review_text(payload: ReviewTextIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        result = moderate_text(payload.content, payload.age_band)
    except ModerationProviderError as exc:
        raise HTTPException(502, str(exc)) from exc
    report = Report(title=payload.title, content_type="text", age_band=payload.age_band,
                    content_text=payload.content, creator_id=user.id,
                    status="human_review", recommendation=result["recommendation"],
                    risk_level=result["risk_level"], findings=result["findings"])
    db.add(report); db.commit(); db.refresh(report)
    return report_out(report)

@router.post("/upload")
async def upload_media(
    title: str = Form(...), age_band: str = Form(...), content_type: str = Form(...),
    file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if age_band not in AGE_BANDS:
        raise HTTPException(400, "Unsupported age band")
    if content_type not in MEDIA_TYPES:
        raise HTTPException(400, "Only image, audio, or video uploads are supported here")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in MEDIA_TYPES[content_type]:
        raise HTTPException(400, f"File extension does not match {content_type} type")
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / safe_name
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_MB * 1024 * 1024:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB limit")
                out.write(chunk)
    finally:
        await file.close()

    result = moderate_media_stub(str(dest), content_type, age_band)
    report = Report(title=title[:250], content_type=content_type, age_band=age_band,
                    file_path=safe_name, creator_id=user.id, status="human_review",
                    recommendation=result["recommendation"], risk_level=result["risk_level"],
                    findings=result["findings"])
    db.add(report); db.commit(); db.refresh(report)
    return report_out(report)

@router.get("")
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Report)
    if user.role == "creator":
        query = query.filter(Report.creator_id == user.id)
    return [report_out(r) for r in query.order_by(Report.created_at.desc()).limit(200).all()]

@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r or (user.role == "creator" and r.creator_id != user.id):
        raise HTTPException(404, "Report not found")
    return report_out(r, include_content=True)

@router.post("/{report_id}/decision")
def decide(report_id: int, payload: ReviewDecisionIn, db: Session = Depends(get_db), reviewer: User = Depends(require_reviewer)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    if payload.action == "approve":
        if r.content_type != "text":
            raise HTTPException(
                409,
                "In-app review for media is not available; inspect the original media before approval.",
            )
        r.status = "approved_by_human"
    elif payload.action == "request_changes":
        r.status = "changes_requested"
    else:
        r.status = "escalated"
    r.reviewer_note = payload.note
    db.commit(); db.refresh(r)
    return report_out(r)
