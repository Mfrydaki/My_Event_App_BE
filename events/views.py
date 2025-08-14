import json
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from bson import ObjectId

from my_events_backend.mongo import get_events_collection
from my_events_backend.auth import optional_jwt
from .models import validate_event, to_mongo_event, event_to_public


@csrf_exempt
@require_http_methods(["GET", "POST"])
@optional_jwt
def events_view(request: HttpRequest):
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
        List of events (GET) or created event (POST).
    """
    events_collection = get_events_collection()

    if request.method == "GET":
        cursor = events_collection.find({}).sort("date", 1)
        event_list = [event_to_public(doc) for doc in cursor]
        return JsonResponse(event_list, safe=False, status=200)

    if not getattr(request, "user_id", None):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        if (request.content_type or "").split(";")[0].strip() != "application/json":
            return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_event(data)
        event_doc = to_mongo_event(data)
        result = events_collection.insert_one(event_doc)
        saved_event = events_collection.find_one({"_id": result.inserted_id})
        return JsonResponse(event_to_public(saved_event), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@optional_jwt
def event_detail_view(request: HttpRequest, event_id: str):
    """
    Retrieve, update, or delete an event by ID.

    GET
    ---
    Public endpoint. Returns one event by ID.

    PUT
    ---
    Protected endpoint. Requires JWT token.
    Updates the event.

    DELETE
    ------
    Protected endpoint. Requires JWT token.
    Deletes the event.

    Parameters
    ----------
    request : HttpRequest
        Django request object.
    event_id : str
        The event's MongoDB ObjectId (as string).

    Returns
    -------
    JsonResponse
        The event (GET), updated event (PUT), or deletion result (DELETE).
    """
    events_collection = get_events_collection()

    try:
        oid = ObjectId(event_id)
    except Exception:
        return JsonResponse({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        event_doc = events_collection.find_one({"_id": oid})
        if not event_doc:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse(event_to_public(event_doc), status=200)

    if not getattr(request, "user_id", None):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "PUT":
        try:
            if (request.content_type or "").split(";")[0].strip() != "application/json":
                return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

            updated_data = json.loads(request.body.decode("utf-8") or "{}")
            validate_event(updated_data)
            update_doc = to_mongo_event(updated_data)
            res = events_collection.update_one({"_id": oid}, {"$set": update_doc})
            if res.matched_count == 0:
                return JsonResponse({"error": "Not found"}, status=404)
            updated_event = events_collection.find_one({"_id": oid})
            return JsonResponse(event_to_public(updated_event), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    res = events_collection.delete_one({"_id": oid})
    if res.deleted_count == 1:
        return JsonResponse({"deleted": True}, status=200)
    return JsonResponse({"error": "Not found"}, status=404)
