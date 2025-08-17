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
    Creates a new event owned by the authenticated user.

    Returns
    -------
    JsonResponse
        200 OK: List of events (GET).
        201 Created: Created event (POST).
        401 Unauthorized: If POST without valid JWT.
        415 Unsupported Media Type: If Content-Type is not JSON.
        400 Bad Request: For validation or other errors.
    """
    events_collection = get_events_collection()

    if request.method == "GET":
        # Step 1: Find all events sorted by date
        cursor = events_collection.find({}).sort("date", 1)
        event_list = [event_to_public(doc) for doc in cursor]
        # Step 2: Return the list
        return JsonResponse(event_list, safe=False, status=200)

    # POST requires authentication
    if not getattr(request, "user_id", None):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Step 1: Check request Content-Type
    if (request.content_type or "").split(";")[0].strip() != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        # Step 2: Parse request body
        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_event(data)

        # Step 3: Prepare event document
        event_doc = to_mongo_event(data)
        event_doc["created_by"] = request.user_id  # set event owner

        # Step 4: Save event in MongoDB
        result = events_collection.insert_one(event_doc)
        saved_event = events_collection.find_one({"_id": result.inserted_id})

        # Step 5: Return the new event
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
    Only the owner (created_by) can update the event.

    DELETE
    ------
    Protected endpoint. Requires JWT token.
    Only the owner (created_by) can delete the event.

    Returns
    -------
    JsonResponse
        200 OK: Event (GET), updated event (PUT), or delete confirmation (DELETE).
        401 Unauthorized: If JWT is missing.
        403 Forbidden: If user is not the owner.
        404 Not Found: If event does not exist.
        415 Unsupported Media Type: If Content-Type is not JSON (PUT only).
        400 Bad Request: Invalid ID or other errors.
    """
    events_collection = get_events_collection()

    # Step 1: Validate event_id
    if not ObjectId.is_valid(event_id):
        return JsonResponse({"error": "Invalid ID"}, status=400)
    oid = ObjectId(event_id)

    # Step 2: Look up the event
    event_doc = events_collection.find_one({"_id": oid})

    # Handle GET
    if request.method == "GET":
        if not event_doc:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse(event_to_public(event_doc), status=200)

    # PUT and DELETE require authentication
    if not getattr(request, "user_id", None):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if not event_doc:
        return JsonResponse({"error": "Not found"}, status=404)

    # Step 3: Check ownership
    if event_doc.get("created_by") != request.user_id:
        return JsonResponse({"error": "Forbidden"}, status=403)

    # Handle PUT
    if request.method == "PUT":
        if (request.content_type or "").split(";")[0].strip() != "application/json":
            return JsonResponse({"error": "Content-Type must be application/json"}, status=415)
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
            validate_event(data)
            update_doc = to_mongo_event(data)
            update_doc.pop("created_by", None)  # do not allow changing owner

            events_collection.update_one({"_id": oid}, {"$set": update_doc})
            updated_event = events_collection.find_one({"_id": oid})
            return JsonResponse(event_to_public(updated_event), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # Handle DELETE
    result = events_collection.delete_one({"_id": oid})
    if result.deleted_count == 1:
        return JsonResponse({"deleted": True}, status=200)
    return JsonResponse({"error": "Not found"}, status=404)
