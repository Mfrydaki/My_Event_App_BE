import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from bson import ObjectId

from my_events_backend.mongo import get_events_collection
from my_events_backend.auth import require_jwt
from .models import validate_event, to_mongo_dict, to_public_dict

@csrf_exempt
@require_http_methods(["GET", "POST"])
@require_jwt
def events_view(request):
    """
    GET: Public - return all events (sorted by date)
    POST: Protected - create new event (requires JWT)
    """
    events_collection = get_events_collection()

    if request.method == "GET":
        cursor = events_collection.find({}).sort("date", 1)
        event_list = [to_public_dict(doc) for doc in cursor]
        return JsonResponse(event_list, safe=False, status=200)

    # POST (protected)
    try:
        if (request.content_type or "").split(";")[0].strip() != "application/json":
            return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_event(data)
        event_doc = to_mongo_dict(data)
        result = events_collection.insert_one(event_doc)
        saved_event = events_collection.find_one({"_id": result.inserted_id})
        return JsonResponse(to_public_dict(saved_event), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@require_jwt
def event_detail_view(request, event_id):
    """
    GET: Public - return one event by ID
    PUT: Protected - update event (requires JWT)
    DELETE: Protected - delete event (requires JWT)
    """
    events_collection = get_events_collection()

    try:
        oid = ObjectId(event_id)
    except Exception:
        return JsonResponse({"error": "invalid ID"}, status=400)

    if request.method == "GET":
        event_doc = events_collection.find_one({"_id": oid})
        if not event_doc:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse(to_public_dict(event_doc), status=200)

    if request.method == "PUT":
        try:
            if (request.content_type or "").split(";")[0].strip() != "application/json":
                return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

            updated_data = json.loads(request.body.decode("utf-8") or "{}")
            validate_event(updated_data)
            update_doc = to_mongo_dict(updated_data)
            res = events_collection.update_one({"_id": oid}, {"$set": update_doc})
            if res.matched_count == 0:
                return JsonResponse({"error": "Not found"}, status=404)
            updated_event = events_collection.find_one({"_id": oid})
            return JsonResponse(to_public_dict(updated_event), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # DELETE
    res = events_collection.delete_one({"_id": oid})
    if res.deleted_count == 1:
        return JsonResponse({"deleted": True}, status=200)
    return JsonResponse({"error": "Not found"}, status=404)
