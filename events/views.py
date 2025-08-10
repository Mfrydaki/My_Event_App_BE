import json
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from bson import ObjectId

from .models import validate_event, to_mongo_dict, to_public_dict
from .mongo import events_collection

@ensure_csrf_cookie  
@csrf_protect 
def events_view(request):

    if request.method == "GET":
        events_data = events_collection.find({})
        event_list = [to_public_dict(event_doc) for event_doc in events_data ]
        return JsonResponse(event_list, safe=False, status=200)

    if request.method == "POST":
        try:
            data_from_frontend = json.loads(request.body.decode("utf-8")) 
            validate_event(data_from_frontend)
            event_to_save = to_mongo_dict(data_from_frontend) 
            insert_result = events_collection.insert_one(event_to_save) 
            saved_event_doc = events_collection.find_one({"_id":insert_result.inserted_id}) 

            return JsonResponse(to_public_dict(saved_event_doc), status=201) 
      
        except Exception as e:
            return JsonResponse({"error": str(e)}, status = 400)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_protect
def event_detail_view(request, event_id):
    try:
        oid = ObjectId(event_id)
    except Exception:
        return JsonResponse({"error":"invalid ID"}, status = 400)
    
    if request.method == "GET":
        event_doc = events_collection.find_one({"_id" :oid})
        if not event_doc:
            return JsonResponse({"error":"Not found"}, status = 404)
        return JsonResponse(to_public_dict(event_doc), status = 200)
    
    if request.method == "PUT":
        try:
            updated_data = json.loads(request.body.decode("utf-8"))
            validate_event(updated_data)
            event_to_update = to_mongo_dict(updated_data)
            events_collection.update_one({"_id":oid}, {"$set": event_to_update})
            updated_event_doc = events_collection.find_one({"_id":oid})
            return JsonResponse(to_public_dict(updated_event_doc), status = 200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status = 400)
    
    if request.method == "DELETE":
        delete_event = events_collection.delete_one({"_id": oid})
        if delete_event.deleted_count == 1:
            return JsonResponse({"deleted" :True}, status = 200)
        return JsonResponse ({"error":"Not found"}, status = 404)

    return JsonResponse({"error": "Method not allowed"}, status=405)
