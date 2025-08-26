import json
from bson import ObjectId
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from my_events_backend.mongo import get_events_collection
from my_events_backend.auth import require_jwt, optional_jwt


def _is_json(request: HttpRequest) -> bool:
    """
    Return True if Content-Type is application/json (ignoring charset).
    """
    return (request.content_type or "").split(";")[0].strip() == "application/json"


@csrf_exempt
@require_http_methods(["GET", "POST"])
def events_view(request: HttpRequest) -> JsonResponse:
    """
    List or create events.

    GET
    ---
    Public endpoint. Returns all events sorted by date.

    POST
    ----
    Protected endpoint. Requires JWT token.
    Creates a new event.

    Parameters
    ----------
    request : HttpRequest
        Django request object.

    Returns
    -------
    JsonResponse
        200 OK: List of events (GET).
        201 Created: Created event (POST).
        415 Unsupported Media Type: If Content-Type is not JSON.
        400 Bad Request: For validation or other errors.
    """
    col = get_events_collection()

    if request.method == "GET":
        cursor = col.find({}, {"_id": 1, "title": 1, "date": 1, "image": 1, "attendees": 1}).sort("date", 1)
        events = []
        for doc in cursor:
            attendees = doc.get("attendees", [])
            events.append({
                "id": str(doc["_id"]),
                "title": doc.get("title", ""),
                "date": doc.get("date", ""),
                "image": doc.get("image", ""),
                "attendees_count": len(attendees) if isinstance(attendees, list) else 0,
            })
        return JsonResponse(events, safe=False, status=200)

    # POST → create event (protected)
    return create_event(request)


@require_http_methods(["POST"])
@require_jwt
def create_event(request: HttpRequest) -> JsonResponse:
    """
    Create a new event.

    POST
    ----
    Protected endpoint. Requires JWT token.

    Parameters
    ----------
    request : HttpRequest
        Django request object.

    Returns
    -------
    JsonResponse
        201 Created: Created event.
        415 Unsupported Media Type: If Content-Type is not JSON.
        400 Bad Request: For validation or other errors.
    """
    if not _is_json(request):
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        title = (data.get("title") or "").strip()
        date = (data.get("date") or "").strip()
        description = (data.get("description") or "").strip()
        image = (data.get("image") or "").strip()

        if not title or not date:
            return JsonResponse({"error": "title and date are required"}, status=400)

        col = get_events_collection()
        doc = {
            "title": title,
            "date": date,
            "description": description,
            "image": image,
            "attendees": [],
            "created_by": str(getattr(request, "user_id", "")),
        }
        res = col.insert_one(doc)
        saved = col.find_one({"_id": res.inserted_id})

        return JsonResponse({
            "id": str(saved["_id"]),
            "title": saved.get("title", ""),
            "date": saved.get("date", ""),
            "description": saved.get("description", ""),
            "image": saved.get("image", ""),
            "attendees_count": 0,
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def event_detail_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """
    Retrieve, update or delete a single event.

    GET
    ---
    Public endpoint. Returns one event by ID.
    If Authorization (JWT) is present & valid, adds `attending: true/false`.

    PUT
    ---
    Protected endpoint. Requires JWT token.

    DELETE
    ------
    Protected endpoint. Requires JWT token.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    event_id : str
        Mongo ObjectId.

    Returns
    -------
    JsonResponse
        200 OK: Event payload (with attendees_count, and attending if JWT).
        400 Bad Request: Invalid ID.
        404 Not Found: If event does not exist.
        415 Unsupported Media Type: If Content-Type is not JSON (PUT).
    """
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    col = get_events_collection()
    oid = ObjectId(event_id)

    if request.method == "GET":
        doc = col.find_one({"_id": oid})
        if not doc:
            return JsonResponse({"error": "Not found"}, status=404)

        raw_attendees = doc.get("attendees") or []
        if not isinstance(raw_attendees, list):
            raw_attendees = []
        attendees = [str(x) for x in raw_attendees]

        data = {
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "date": doc.get("date", ""),
            "description": doc.get("description", ""),
            "image": doc.get("image", ""),
            "attendees_count": len(attendees),
        }

        try:
            if optional_jwt:
                user = optional_jwt(request)  # expected dict with "id"
                if user and user.get("id"):
                    data["attending"] = str(user["id"]) in attendees
        except Exception:
            pass

        return JsonResponse(data, status=200)

    if request.method == "PUT":
        return update_event(request, oid)

    return delete_event(request, oid)
    # DELETE
    return delete_event(request, oid)


@require_http_methods(["PUT"])
@require_jwt
def update_event(request: HttpRequest, oid: ObjectId) -> JsonResponse:
    """
    Update an existing event.

    PUT
    ---
    Protected endpoint. Requires JWT token.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    oid : ObjectId
        Mongo ObjectId of the event.

    Returns
    -------
    JsonResponse
        200 OK: Updated event.
        415 Unsupported Media Type: If Content-Type is not JSON.
        404 Not Found: If event does not exist.
        400 Bad Request: For other errors.
    """
    if not _is_json(request):
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        updates = {}
        for k in ("title", "date", "description", "image"):
            if k in data:
                updates[k] = (data[k] or "").strip()

        if not updates:
            return JsonResponse({"error": "No fields to update"}, status=400)

        col = get_events_collection()
        col.update_one({"_id": oid}, {"$set": updates})
        doc = col.find_one({"_id": oid})
        if not doc:
            return JsonResponse({"error": "Not found"}, status=404)

        attendees = [str(x) for x in (doc.get("attendees") or []) if isinstance(doc.get("attendees"), list)]
        return JsonResponse({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "date": doc.get("date", ""),
            "description": doc.get("description", ""),
            "image": doc.get("image", ""),
            "attendees_count": len(attendees),
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_http_methods(["DELETE"])
@require_jwt
def delete_event(request: HttpRequest, oid: ObjectId) -> HttpResponse:
    """
    Delete an event.

    DELETE
    ------
    Protected endpoint. Requires JWT token.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    oid : ObjectId
        Mongo ObjectId of the event.

    Returns
    -------
    HttpResponse
        204 No Content on success.
    """
    col = get_events_collection()
    col.delete_one({"_id": oid})
    return HttpResponse(status=204)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def attend_event_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """
    Attend an event.

    POST
    ----
    Protected endpoint. Requires JWT token.
    Adds the authenticated user to the event's attendee list.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    event_id : str
        Mongo ObjectId.

    Returns
    -------
    JsonResponse
        200 OK: { "message": "Joined", "attendees_count": int }
        400 Bad Request: Invalid ID.
        404 Not Found: Event not found.
        409 Conflict: Already attending.
    """
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    user_id = str(getattr(request, "user_id", ""))
    col = get_events_collection()
    oid = ObjectId(event_id)

    doc = col.find_one({"_id": oid}, {"_id": 1, "attendees": 1})
    if not doc:
        return JsonResponse({"error": "Not found"}, status=404)

    res = col.update_one({"_id": oid}, {"$addToSet": {"attendees": user_id}})
    if res.modified_count == 0:
        return JsonResponse({"error": "Already attending"}, status=409)

    fresh = col.find_one({"_id": oid}, {"attendees": 1})
    return JsonResponse({"message": "Joined", "attendees_count": len(fresh.get("attendees", []))}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def unattend_event_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """
    Unattend an event.

    POST
    ----
    Protected endpoint. Requires JWT token.
    Removes the authenticated user from the event's attendee list.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    event_id : str
        Mongo ObjectId.

    Returns
    -------
    JsonResponse
        200 OK: { "message": "Left", "attendees_count": int }
        400 Bad Request: Invalid ID.
        404 Not Found: Event not found.
        409 Conflict: Not attending.
    """
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    user_id = str(getattr(request, "user_id", ""))
    col = get_events_collection()
    oid = ObjectId(event_id)

    doc = col.find_one({"_id": oid}, {"_id": 1, "attendees": 1})
    if not doc:
        return JsonResponse({"error": "Not found"}, status=404)

    res = col.update_one({"_id": oid}, {"$pull": {"attendees": user_id}})
    if res.modified_count == 0:
        return JsonResponse({"error": "Not attending"}, status=409)

    fresh = col.find_one({"_id": oid}, {"attendees": 1})
    return JsonResponse({"message": "Left", "attendees_count": len(fresh.get("attendees", []))}, status=200)
