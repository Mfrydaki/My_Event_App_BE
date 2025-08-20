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
    Public endpoint. Expects JSON with at least email and password.
    Password is stored hashed using Django hashers.
    Fails with 409 if email already exists (unique index on 'email').

    Returns
    -------
    JsonResponse
        201 Created: {"user": <public_user>} on success.
        409 Conflict: If email already exists.
        415 Unsupported Media Type: If Content-Type is not application/json.
        400 Bad Request: For validation or other errors.
    """
    # Step 1: Check request Content-Type
    if (request.content_type or "").split(";")[0].strip() != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        # Step 2: Parse request body
        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_register(data)

        # Step 3: Prepare user document
        user_doc = to_mongo_user(data)
        users_collection = get_users_collection()

        # Step 4: Save in MongoDB
        result = users_collection.insert_one(user_doc)
        saved = users_collection.find_one({"_id": result.inserted_id})

        # Step 5: Return the new user (without token here)
        return JsonResponse({"user": user_to_public(saved)}, status=201)

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
    Public endpoint. Expects JSON with email and password.
    Verifies password against stored hash.
    On success, returns public user data and a JWT access token.

    Returns
    -------
    JsonResponse
        200 OK: {"user": <public_user>, "access": <jwt>} on success.
        401 Unauthorized: If credentials are invalid.
        415 Unsupported Media Type: If Content-Type is not application/json.
        400 Bad Request: For validation or other errors.
    """
    # Step 1: Check request Content-Type
    if (request.content_type or "").split(";")[0].strip() != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json"}, status=415)

    try:
        # Step 2: Parse request body
        data = json.loads(request.body.decode("utf-8") or "{}")
        validate_login(data)

        email = data["email"].strip().lower()
        password = data["password"]

        # Step 3: Find user in MongoDB
        users_collection = get_users_collection()
        doc = users_collection.find_one({"email": email})

        # Step 4: Check password
        if not doc or not verify_password(doc.get("password", ""), password):
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        # Step 5: Create JWT token
        token = make_access_token(str(doc["_id"]), doc["email"])

        # Step 6: Return user and token
        return JsonResponse({"user": user_to_public(doc), "access": token}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
@require_jwt
def profile_view(request):
    """
    Get the authenticated user's profile.

    GET
    ---
    Protected endpoint. Requires JWT token in Authorization header as "Bearer <token>".
    Reads the user id from the JWT "sub" claim and returns the public user data.

    Returns
    -------
    JsonResponse
        200 OK: Public user dict (id, email, first_name, last_name, date_of_birth).
        404 Not Found: If the user does not exist in the database.
        401 Unauthorized: If JWT is missing or invalid (handled by @require_jwt).
        400 Bad Request: If the user id is not a valid ObjectId.
    """
    try:
        # Step 1: Get user id from JWT
        user_id = request.jwt.get("sub")
        if not ObjectId.is_valid(user_id):
            return JsonResponse({"error": "Invalid user id"}, status=400)

        # Step 2: Find user in MongoDB
        users_collection = get_users_collection()
        doc = users_collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return JsonResponse({"error": "Not found"}, status=404)

        # Step 3: Return public user data
        return JsonResponse({"user" : user_to_public(doc)}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
