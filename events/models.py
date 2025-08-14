from datetime import datetime, date
from typing import Dict, Any, Mapping, Optional
import re

MAX_TITLE_LENGTH = 200
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_event(d: Dict[str, Any]) -> None:
    """
    Validate event data before saving to MongoDB.

    Parameters
    ----------
    d : dict
    Event data dictionary.

    Raises
    ------
    ValueError
    If validation fails (missing title, invalid date, etc.).
    """
    title = str(d.get("title", "") or "").strip()
    if not title:
        raise ValueError("Title is required")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title max length is {MAX_TITLE_LENGTH}")

    if "date" not in d:
        raise ValueError("Date is required")

    date_str = str(d["date"] or "").strip()
    if not _ISO_DATE_RE.match(date_str):
        raise ValueError("Date must be ISO string: YYYY-MM-DD")
    try:
        date.fromisoformat(date_str)
    except Exception:
        raise ValueError("Invalid calendar date (use real YYYY-MM-DD)")


def to_mongo_dict(d: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Prepare a clean dict for MongoDB insert/update.

    Parameters
    ----------
    d : Mapping[str, Any]
    Event data.

    Returns
    -------
    dict
    Sanitized event data for MongoDB storage.
    """
    return {
        "title": str(d.get("title", "") or "").strip(),
        "description": str(d.get("description", "") or "").strip(),
        "details": str(d.get("details", "") or "").strip(),
        "date": str(d.get("date", "") or "").strip(),
        "image": str(d.get("image", "") or "").strip(),
    }


def to_public_dict(event_doc: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Convert a MongoDB event document into a public-facing dictionary.

    Parameters
    ----------
    event_doc : Mapping[str, Any]
    The event document from MongoDB.

    Returns
    -------
    dict
    Public-safe event dictionary.
    """
    _id = event_doc.get("_id")
    id_str: Optional[str] = str(_id) if _id is not None else None

    raw_date = event_doc.get("date")
    date_str = ""
    if isinstance(raw_date, datetime):
        date_str = raw_date.date().isoformat()
    elif isinstance(raw_date, date):
        date_str = raw_date.isoformat()
    elif isinstance(raw_date, str):
        raw_date = raw_date.strip()
        if "T" in raw_date:
            try:
                date_str = datetime.fromisoformat(raw_date).date().isoformat()
            except Exception:
                date_str = raw_date
        else:
            date_str = raw_date

    return {
        "id": id_str,
        "title": str(event_doc.get("title", "") or "").strip(),
        "description": str(event_doc.get("description", "") or "").strip(),
        "details": str(event_doc.get("details", "") or "").strip(),
        "date": date_str,
        "image": str(event_doc.get("image", "") or "").strip(),
    }
