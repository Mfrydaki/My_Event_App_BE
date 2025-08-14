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
    """
    Create a new user account.

    POST
    ----
    - Public endpoint (no authentication required).
    - Expects JSON body with at least `email` and `password`.
    - Password is stored hashed using Django hashers.
    - Fails with HTTP 409 if email already exists.
    - On success, returns public user data and a JWT accesstoken.

    Returns
    -------
    JsonResponse
    201 Created: {"user": <public_user>, "access": <jwt>} on success.
    409 Conflict if email already exists.
    400 Bad Request for validation or other errors.
    
    if (request.content_type or "").split(";")[0].strip() != "application/json":
    return JsonResponse({"error": "Content-Type must be application/json"}, status=415)
    """
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
    """
    Authenticate an existing user and return an access token.

    POST
    ----
    - Public endpoint (no authentication required).
    - Expects JSON body with `email` and `password`.
    - Verifies password against stored hash.
    - On success, returns public user data and a JWT access token.

    Returns
    -------
    JsonResponse
        200 OK: {"user": <public_user>, "access": <jwt>} on success.
        401 Unauthorized if credentials are invalid.
        400 Bad Request for validation or other errors.
    """
    if (request.content_type or "").split(";")[0].strip() != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

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
    
@csrf_exempt
@require_http_methods(["GET"])
@require_jwt
def me_view(request):
    """
    Get the authenticated user's profile.

    GET
    ---
    - Protected endpoint (requires JWT in `Authorization` header as `Bearer <token>`).
    - Reads user ID from token and returns public user data.

    Returns
    -------
    JsonResponse
        200 OK: {"id": ..., "email": ..., "first_name": ..., "last_name": ..., "date_of_birth": ...}
        404 Not Found if the user does not exist in the database.
        401 Unauthorized if JWT is missing or invalid.
    """
    col = get_users_collection()
    user_id = request.jwt.get("sub")

    try:
        doc = col.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse(user_to_public(doc), status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

