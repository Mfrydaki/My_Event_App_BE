
from datetime import datetime, date
from typing import Dict, Any, Mapping, Optional
import re

MAX_TITLE_LENGTH = 200
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_event(d: Dict[str, Any], partial :bool =False) -> None:
    """
    Validate event data before saving to MongoDB.

    Notes
    -----
    - Ensures "title" exists and respects MAX_TITLE_LENGTH.
    - Ensures "date" exists and is a valid ISO calendar date (YYYY-MM-DD).

    Parameters
    ----------
    d : dict
    Event data dictionary.
    partial: bool, optional
    If True, validate only provided fields(for partial updates).

    Returns
    -------
    None
    Function completes silently if validation passes.

    Raises
    ------
    ValueError
    If validation fails (missing title, invalid date, etc.).
    """
    if (not partial) or ("title" in d):
     title = str(d.get("title", "") or "").strip()
    if not title:
        raise ValueError("Title is required")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title max length is {MAX_TITLE_LENGTH}")
    

    if (not partial) or ("date" in d):
        if "date" not in d and not partial:
            raise ValueError("Date is required")
        date_str = str(d.get("date", "") or "").strip()
        if not _ISO_DATE_RE.fullmatch(date_str):
            raise ValueError("Date must be ISO string: YYYY-MM-DD")
        try:
            date.fromisoformat(date_str)  # validates calendar correctness
        except Exception:
            raise ValueError("Invalid calendar date (use real YYYY-MM-DD)")



def to_mongo_event(d: Mapping[str, Any], partial: bool = False) -> Dict[str, Any]:
    """
    Convert incoming event data into a MongoDB-ready document.

    Notes
    -----
    - Trims whitespace.
    - Keeps "date" as ISO string (YYYY-MM-DD) for simple lexicographic sorting.
    - Does not set "created_by"; views should attach the authenticated user id.
    -When partial= True, only includes keys present in "d".

    Parameters
    ----------
    d : Mapping[str, Any]
    Event data.
    partial: bool, optional 
    If True, return only provided fields(for partial updates).

    Returns
    -------
    dict
    Sanitized event document for MongoDB storage.
    """
    
    fields = ("title", "description", "details", "date", "image")
    out: Dict[str, Any] = {}

    def clean(s: Any) -> str:
        return str(s or "").strip()

    if partial:
        for k in fields:
            if k in d:
                out[k] = clean(d.get(k))
        return out

    # full document (create)
    return {
        "title": clean(d.get("title")),
        "description": clean(d.get("description")),
        "details": clean(d.get("details")),
        "date": clean(d.get("date")),
        "image": clean(d.get("image")),
        # "created_by": <to be set in the view using request.user_id>
    }


def event_to_public(event_doc: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Convert a MongoDB event document into a public-facing dictionary.

    Notes
    -----
    - Converts "_id" (ObjectId) to string.
    - Normalizes date to ISO string (YYYY-MM-DD) if stored as datetime/date or ISO datetime.
    - Ensures 'attendees' is always a list of strings (user ids).

    Parameters
    ----------
    event_doc : Mapping[str, Any]
    The event document from MongoDB.

    Returns
    -------
    dict
    Public-safe event dictionary ready for API responses.
    """
    _id = event_doc.get("_id")
    id_str: Optional[str] = str(_id) if _id is not None else None

    raw_date = event_doc.get("date")
    date_str = str(raw_date or "").strip()

    if isinstance(raw_date, datetime):
        date_str = raw_date.date().isoformat()
    elif isinstance(raw_date, date):
        date_str = raw_date.isoformat()
    elif isinstance(raw_date, str):
        s = raw_date.strip()
        if "T" in s:
            # handle ISO datetime strings e.g. 2025-08-14T10:00:00
            try:
                date_str = datetime.fromisoformat(s).date().isoformat()
            except Exception:
                date_str = s
        else:
            date_str = s

    attendees = event_doc.get("attendees", [])
    if not isinstance(attendees, list):
        attendees = []

    return {
        "id": id_str,
        "title": str(event_doc.get("title", "") or "").strip(),
        "description": str(event_doc.get("description", "") or "").strip(),
        "details": str(event_doc.get("details", "") or "").strip(),
        "date": date_str,
        "image": str(event_doc.get("image", "") or "").strip(),
        "created_by": str(event_doc.get("created_by", "") or "").strip(),
        "attendees": [str(uid) for uid in attendees],
    }
