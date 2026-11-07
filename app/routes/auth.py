from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import PasswordChangeIn, ProfileUpdateIn, RegisterIn, TokenOut
from ..security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), role="creator")
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_access_token(user.id)}

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id)}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}

@router.patch("/me")
def update_profile(payload: ProfileUpdateIn, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    email = str(payload.email).lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user and existing_user.id != user.id:
        raise HTTPException(status_code=409, detail="Email already registered")
    user.email = email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}

@router.post("/change-password")
def change_password(payload: PasswordChangeIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
