# users/models.py
from typing import Dict, Any, Mapping, Optional
import re
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def validate_register(d: Dict[str, Any]) -> None:
    """
    Validate registration data for creating a new user.

    Notes
    -----
    - Checks that `email` is valid and not empty.
    - Checks that `password` is provided.

    Returns
    -------
    None
    Function completes silently if validation passes.

    Raises
    ------
    ValueError
    If `email` is invalid or missing.
    If `password` is missing.
    """
    
    email = str(d.get("email", "") or "").strip().lower()
    password = str(d.get("password", "") or "")
    if not email or not EMAIL_RE.match(email):
        raise ValueError("Valid email is required")
    if not password:
        raise ValueError("Password is required")

def validate_login(d: Dict[str, Any]) -> None:
 """
Validate login data for authenticating a user.

Notes
    -----
- Checks that `email` is valid and not empty.
 - Checks that `password` is provided.

Returns
-------
None
Function completes silently if validation passes.

Raises
------
ValueError
If `email` is invalid or missing.
If `password` is missing.
"""
    
 email = str(d.get("email", "") or "").strip().lower()
 password = str(d.get("password", "") or "")
 if not email or not EMAIL_RE.match(email):
        raise ValueError("Valid email is required")
 if not password:
        raise ValueError("Password is required")

def to_mongo_user(d: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Convert registration data into a MongoDB user document.

    Notes
    -----
    - Lowercases the `email`.
    - Hashes the `password` using Django hashers.
    - Strips extra spaces from optional fields.

    Parameters
    ----------
    d : Mapping
        Dictionary-like object with at least `email` and `password`.

    Returns
    -------
    dict
        A MongoDB-ready user document for insertion.
    """
    return {
        "email": str(d["email"]).strip().lower(),
        "password": make_password(str(d["password"])),
        "first_name": str(d.get("first_name", "") or "").strip(),
        "last_name": str(d.get("last_name", "") or "").strip(),
        "date_of_birth": str(d.get("date_of_birth", "") or "").strip() or None,
    }

def user_to_public(doc: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Convert a MongoDB user document into a public-facing dictionary.

    Notes
    -----
    - Converts `_id` (ObjectId) to string.
    - Excludes sensitive fields like `password`.

    Parameters
    ----------
    doc : Mapping
        MongoDB user document.

    Returns
    -------
    dict
        Public-safe user data ready for API responses.
    """
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
    """
    Check if a raw password matches the stored hashed password.

    Parameters
    ----------
    hashed : str
        The hashed password from the database.
    raw : str
        The plain text password to verify.

    Returns
    -------
    bool
        True if the password matches, False otherwise.
    """
    return check_password(raw, hashed)
