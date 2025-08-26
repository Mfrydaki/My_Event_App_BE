# import json
# from django.http import JsonResponse, HttpRequest
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from bson import ObjectId

# from my_events_backend.mongo import get_events_collection
# from my_events_backend.auth import( optional_jwt, require_jwt, decode_token,_get_token_from_request)
# from .models import validate_event, to_mongo_event, event_to_public

# def _is_json(request: HttpRequest) -> bool:
#     """
#     Return True if Content-Type is application/json (ignoring charset).
#     """
#     return (request.content_type or "").split(";")[0].strip() == "application/json"

# @csrf_exempt
# @require_http_methods(["GET", "POST"])
# def events_view(request: HttpRequest) ->JsonResponse:
#     """
#     List or create events.

#     GET
#     ---
#     Public endpoint. Returns all events sorted by date.

#     POST
#     ----
#     Protected endpoint. Requires JWT token.
#     Creates a new event.

#     Parameters
#     ----------
#     request : HttpRequest
#     Django request object.

#     Returns
#     -------
#     JsonResponse
#         200 OK: List of events (GET).
#         201 Created: Created event (POST).
#         401 Unauthorized: If POST without valid JWT.
#         415 Unsupported Media Type: If Content-Type is not JSON.
#         400 Bad Request: For validation or other errors.
#     """
#     events_collection = get_events_collection()

#     if request.method == "GET":
#         cursor = events_collection.find({}).sort("date", 1)
#         event_list = [event_to_public(doc) for doc in cursor]
#         return JsonResponse(event_list, safe=False, status=200)
    
#     user_id = getattr(request, "user_id", None)

#     if not user_id:
#         token = _get_token_from_request(request)
#         if not token:
#             return JsonResponse({"error": "Unauthorized"}, status=401)

#         try:
#             claims = decode_token(token)
#             user_id = claims.get("sub")
#         except Exception:
#             return JsonResponse({"error": "Unauthorized"}, status=401)

    
#     if not _is_json(request):
#         return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

#     try:
#         data = json.loads(request.body.decode("utf-8") or "{}")
#         validate_event(data)

#         event_doc = to_mongo_event(data)
#         event_doc["created_by"] = str(user_id)
#         event_doc.setdefault( "attendees",[])

#         result = events_collection.insert_one(event_doc)
#         saved_event = events_collection.find_one({"_id": result.inserted_id})
#         return JsonResponse(event_to_public(saved_event), status=201)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=400)


# @csrf_exempt
# @require_http_methods(["GET", "PUT", "DELETE"])
# @require_jwt
# def event_detail_view(request: HttpRequest, event_id: str):
#     """
#     Retrieve, update, or delete an event by ID.

#     GET
#     ---
#     Public endpoint. Returns one event by ID.

#     PUT
#     ---
#     Protected endpoint. Requires JWT token.
#     Only the owner (created_by) can update the event.

#     DELETE
#     ------
#     Protected endpoint. Requires JWT token.
#     Only the owner (created_by) can delete the event.

#     Returns
#     -------
#     JsonResponse
#         200 OK: Event (GET), updated event (PUT), or delete confirmation (DELETE).
#         401 Unauthorized: If JWT is missing.
#         403 Forbidden: If user is not the owner.
#         404 Not Found: If event does not exist.
#         415 Unsupported Media Type: If Content-Type is not JSON (PUT only).
#         400 Bad Request: Invalid ID or other errors.
#     """
#     events_collection = get_events_collection()

#     if not ObjectId.is_valid(event_id):
#         return JsonResponse({"error": "Invalid ID"}, status=400)
#     oid = ObjectId(event_id)

#     event_doc = events_collection.find_one({"_id": oid})

#     if request.method == "GET":
#         if not event_doc:
#             return JsonResponse({"error": "Not found"}, status=404)
#         return JsonResponse(event_to_public(event_doc), status=200)
    
#     # For PUT/DELETE: must exist and must be owned by current user
#     if not event_doc:
#         return JsonResponse({"error": "Not found"}, status=404)

#     # Owner check (tolerant to string/ObjectId types)
#     if str(event_doc.get("created_by", "")) != str(request.user_id):
#         return JsonResponse({"error": "Forbidden"}, status=403)

#     if request.method == "PUT":
#         if not _is_json(request):
#             return JsonResponse({"error": "Content-Type must be application/json"}, status=415)
#         try:
#             data = json.loads(request.body.decode("utf-8") or "{}")
#             validate_event(data, partial = True) 

#             #Never allow identity/ownership changes
#             update_doc = to_mongo_event(data, partial= True)
#             update_doc.pop ("id", None)
#             update_doc.pop("created_by", None)

#             if update_doc:
#                 events_collection.update_one({"_id": oid}, {"$set": update_doc})
#             updated_event = events_collection.find_one({"_id": oid})
#             return JsonResponse(event_to_public(updated_event), status=200)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)

#     result = events_collection.delete_one({"_id": oid})
#     if result.deleted_count == 1:
#         return JsonResponse({"deleted": True}, status=200)
#     return JsonResponse({"error": "Not found"}, status=404)

# @csrf_exempt
# @require_http_methods(["POST"])
# @require_jwt
# def attend_event_view(request: HttpRequest, event_id: str):
#     """
#     Attend an event.

#     POST
#     ----
#     Protected endpoint. Requires JWT token.
#     Adds the authenticated user to the event's attendee list.

#     Returns
#     -------
#     JsonResponse
#         200 OK: Updated event with new attendee.
#         400 Bad Request: Invalid ID.
#         404 Not Found: Event not found.
#     """
#     events_collection = get_events_collection()

#     if not ObjectId.is_valid(event_id):
#         return JsonResponse({"error": "Invalid event id"}, status=400)
#     oid = ObjectId(event_id)

#     event = events_collection.find_one({"_id": oid})
#     if not event:
#         return JsonResponse({"error": "Event not found"}, status=404)

#     events_collection.update_one({"_id": oid}, {"$addToSet": {"attendees": str(request.user_id)}})
#     updated = events_collection.find_one({"_id": oid})
#     return JsonResponse(event_to_public(updated), status=200)

# @csrf_exempt
# @require_http_methods(["POST"])
# @require_jwt
# def unattend_event_view(request: HttpRequest, event_id: str):
#     """
#     Unattend an event.

#     POST
#     ----
#     Protected endpoint. Requires JWT token.
#     Removes the authenticated user from the event's attendee list.

#     Returns
#     -------
#     JsonResponse
#         200 OK: Updated event without the user in attendees.
#         400 Bad Request: Invalid ID.
#         404 Not Found: Event not found.
#     """
#     events_collection = get_events_collection()

#     if not ObjectId.is_valid(event_id):
#         return JsonResponse({"error": "Invalid event id"}, status=400)
#     oid = ObjectId(event_id)

#     event = events_collection.find_one({"_id": oid})
#     if not event:
#         return JsonResponse({"error": "Event not found"}, status=404)
    
#     events_collection.update_one({"_id": oid}, {"$pull": {"attendees": str(request.user_id)}})
#     updated = events_collection.find_one({"_id": oid})
#     return JsonResponse(event_to_public(updated), status=200)

import json
from bson import ObjectId
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from my_events_backend.mongo import get_events_collection
from my_events_backend.auth import require_jwt


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
    """
    col = get_events_collection()

    if request.method == "GET":
        cursor = col.find({}, {"_id": 1, "title": 1, "date": 1, "image": 1}).sort("date", 1)
        events = [
            {
                "id": str(doc["_id"]),
                "title": doc.get("title", ""),
                "date": doc.get("date", ""),
                "image": doc.get("image", ""),
            }
            for doc in cursor
        ]
        return JsonResponse(events, safe=False, status=200)

    # POST → create event (protected)
    return create_event(request)


@require_http_methods(["POST"])
@require_jwt
def create_event(request: HttpRequest) -> JsonResponse:
    """Helper for POST /events/"""
    if (request.content_type or "").split(";")[0].strip() != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        title = (data.get("title") or "").strip()
        date = (data.get("date") or "").strip()
        description = (data.get("description") or "").strip()
        image = (data.get("image") or "").strip()

        if not title or not date:
            return JsonResponse({"error": "title and date are required"}, status=400)

        doc = {
            "title": title,
            "date": date,
            "description": description,
            "image": image,
            "attendees": [],
        }
        col = get_events_collection()
        res = col.insert_one(doc)
        saved = col.find_one({"_id": res.inserted_id})

        return JsonResponse({
            "id": str(saved["_id"]),
            "title": saved.get("title", ""),
            "date": saved.get("date", ""),
            "description": saved.get("description", ""),
            "image": saved.get("image", ""),
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_http_methods(["GET", "PUT", "DELETE"])
def event_detail_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """
    Retrieve, update or delete a single event.
    """
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    col = get_events_collection()
    oid = ObjectId(event_id)

    if request.method == "GET":
        doc = col.find_one({"_id": oid})
        if not doc:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "date": doc.get("date", ""),
            "description": doc.get("description", ""),
            "image": doc.get("image", ""),
        }, status=200)

    if request.method == "PUT":
        return update_event(request, oid)

    # DELETE
    return delete_event(oid)


@require_http_methods(["PUT"])
@require_jwt
def update_event(request: HttpRequest, oid: ObjectId) -> JsonResponse:
    """Helper for PUT /events/:id/"""
    if (request.content_type or "").split(";")[0].strip() != "application/json":
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

        return JsonResponse({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "date": doc.get("date", ""),
            "description": doc.get("description", ""),
            "image": doc.get("image", ""),
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_http_methods(["DELETE"])
@require_jwt
def delete_event(oid: ObjectId) -> JsonResponse:
    """Helper for DELETE /events/:id/"""
    col = get_events_collection()
    col.delete_one({"_id": oid})
    return JsonResponse({}, status=204)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def attend_event_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """Attend an event (add user_id to attendees)."""
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    user_id = getattr(request, "user_id", None)
    col = get_events_collection()
    res = col.update_one({"_id": ObjectId(event_id)}, {"$addToSet": {"attendees": user_id}})
    if res.matched_count == 0:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"status": "ok"}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def unattend_event_view(request: HttpRequest, event_id: str) -> JsonResponse:
    """Unattend an event (remove user_id from attendees)."""
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid event id"}, status=400)

    user_id = getattr(request, "user_id", None)
    col = get_events_collection()
    res = col.update_one({"_id": ObjectId(event_id)}, {"$pull": {"attendees": user_id}})
    if res.matched_count == 0:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"status": "ok"}, status=200)
