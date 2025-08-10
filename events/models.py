from datetime import datetime, date
from typing import  Dict , Any

def validate_event(d: Dict[str, Any]) -> None:
    """
    Basic validation before saving to MongoDB.
    - We require a non-empty title (max 200 chars).
    - We require a date in 'YYYY-MM-DD' format (ISO string).
    """
    title = str(d.get("title", "")).strip()
    if not title:
        raise ValueError("Title is required")
    if len(title) > 200:
        raise ValueError("Title max lenght is 200")
    
    if "date" not in d:
        raise ValueError("Date is required")
    try:
        datetime.fromisoformat(str(d["date"])).date()
    except Exception:
        raise ValueError("Date must be ISO string: YYYY-MM-DD")
    
def to_mongo_dict(d):
    """
    Prepare a clean dict for MongoDB insert/update.
    - Trim title.
    - Keep date as an ISO string (easy for React/JSON).
    """
    return{
         "title": str(d.get("title", "")).strip(),
         "description" : str(d.get("description", "")),
         "details": str(d.get("details","")),
         "date" : str(d.get("date","")),
         "image": str(d.get("image",""))
     }
def to_public_dict(event_doc):
    """
    Prepare a clean dict for MongoDB insert/update.
    - Trim title.
    - Keep date as an ISO string (easy for React/JSON).
    """
    _id = event_doc.get("_id")
    id_str = str(_id) if _id else None
     
    raw_date = event_doc.get("date")
    if isinstance(raw_date, (datetime, date)):
        date_str = raw_date.isoformat()
    else:
        date_str = str(raw_date) if raw_date is not None else ""
    
    return{

        "id" : id_str,
        "title": event_doc.get("title",""),
        "description": event_doc.get("description",""),
        "details": event_doc.get("details",""),
        "date": date_str,
        "image": event_doc.get("image","")

    }



     




