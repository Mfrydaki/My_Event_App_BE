# users/models.py
from typing import Dict, Any, Mapping, Optional
import re
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def validate_register(d: Dict[str, Any]) -> None:
    email = str(d.get("email", "") or "").strip().lower()
    password = str(d.get("password", "") or "")
    if not email or not EMAIL_RE.match(email):
        raise ValueError("Valid email is required")
    if not password:
        raise ValueError("Password is required")
    # προαιρετικά: min length, complexity, κλπ.

def validate_login(d: Dict[str, Any]) -> None:
    email = str(d.get("email", "") or "").strip().lower()
    password = str(d.get("password", "") or "")
    if not email or not EMAIL_RE.match(email):
        raise ValueError("Valid email is required")
    if not password:
        raise ValueError("Password is required")

def to_mongo_user(d: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "email": str(d["email"]).strip().lower(),
        "password": make_password(str(d["password"])),
        "first_name": str(d.get("first_name", "") or "").strip(),
        "last_name": str(d.get("last_name", "") or "").strip(),
        "date_of_birth": str(d.get("date_of_birth", "") or "").strip() or None,
    }

def user_to_public(doc: Mapping[str, Any]) -> Dict[str, Any]:
    _id = doc.get("_id")
    uid: Optional[str] = str(_id) if isinstance(_id, ObjectId) else (str(_id) if _id else None)
    return {
        "id": uid,
        "email": str(doc.get("email", "") or "").lower(),
        "first_name": str(doc.get("first_name", "") or ""),
        "last_name": str(doc.get("last_name", "") or ""),
        "date_of_birth": doc.get("date_of_birth") or None,
    }

def verify_password(hashed: str, raw: str) -> bool:
    return check_password(raw, hashed)
