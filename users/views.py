# users/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from my_events_backend.mongo import get_users_collection
from my_events_backend.auth import make_access_token, require_jwt
from .models import (
    validate_register, validate_login,
    to_mongo_user, user_to_public, verify_password
)

@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_register(data)
        user_doc = to_mongo_user(data)
        col = get_users_collection()
        result = col.insert_one(user_doc)  # θα ρίξει DuplicateKeyError αν υπάρχει ίδιο email
        saved = col.find_one({"_id": result.inserted_id})
        # auto-login προαιρετικά:
        token = make_access_token(str(saved["_id"]), saved["email"])
        return JsonResponse({"user": user_to_public(saved), "access": token}, status=201)
    except DuplicateKeyError:
        return JsonResponse({"error": "Email already exists"}, status=409)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_login(data)
        email = data["email"].strip().lower()
        password = data["password"]
        col = get_users_collection()
        doc = col.find_one({"email": email})
        if not doc or not verify_password(doc.get("password", ""), password):
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        token = make_access_token(str(doc["_id"]), doc["email"])
        return JsonResponse({"user": user_to_public(doc), "access": token}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
