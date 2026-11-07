import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..services.rule_engine import RULE_BOOK_DIRECTORY

router = APIRouter(prefix="/api/rule-book", tags=["Rule book"])


@router.get("/{book_name}", response_class=FileResponse)
def get_rule_book(book_name: str):
    if not re.fullmatch(r"[a-z0-9_-]+", book_name):
        raise HTTPException(404, "Rule book not found.")
    rule_book = RULE_BOOK_DIRECTORY / f"{book_name}.json"
    if not rule_book.is_file():
        raise HTTPException(404, "Rule book not found.")
    return FileResponse(rule_book, media_type="application/json")
