# my_events_backend/auth.py
import os, time, jwt
from functools import wraps
from django.http import JsonResponse

JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-prod")
JWT_ALG = "HS256"
ACCESS_MIN = int(os.environ.get("JWT_ACCESS_MINUTES", "30"))
LEeway_SEC = 30  # small clock skew tolerance

def make_access_token(user_id: str, email: str) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id (str): The unique identifier of the user (usually a database ID).
        email (str): The user's email address.

    Returns:
        str: Encoded JWT token string.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": (email or "").lower(),
        "iat": now,  # issued at
        "exp": now + ACCESS_MIN * 60,  # expiration timestamp
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str):
    """
    Decode and validate a JWT token.

    Args:
        token (str): The JWT token string to decode.

    Returns:
        dict: The decoded claims (payload).

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid or has bad signature.
    """
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALG],
        options={"require": ["exp", "iat"]},
        leeway=LEeway_SEC,
    )

def _extract_bearer_token(request):
    """
    Extract the Bearer token from the Authorization header.

    Args:
        request (HttpRequest): The Django HTTP request object.

    Returns:
        str | None: The token string if found, otherwise None.
    """
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    parts = auth.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None

def require_jwt(view_func):
    """
    Decorator to require a valid JWT access token for a view.

    - Returns HTTP 401 if no valid Bearer token is provided.
    - Sets `request.jwt` to the decoded claims.
    - Sets `request.user_id` to the `sub` claim.

    Usage:
        @require_jwt
        def protected_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = _extract_bearer_token(request)
        if not token:
            return JsonResponse({"error": "Missing Bearer token"}, status=401)
        try:
            claims = decode_token(token)
            if claims.get("type") != "access":
                return JsonResponse({"error": "Invalid token type"}, status=401)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)

        request.jwt = claims
        request.user_id = claims.get("sub")
        return view_func(request, *args, **kwargs)
    return wrapper

def optional_jwt(view_func):
    """
    Decorator to optionally accept a JWT token for a view.

    - If a valid Bearer token is provided, sets `request.jwt` and `request.user_id`.
    - If no token is provided (or it is invalid), continues without raising 401.
    - Useful for public GET endpoints that can be accessed by both authenticated
      and unauthenticated users.

    Usage:
        @optional_jwt
        def public_view(request):
            if request.user_id:
                # Authenticated user
                ...
            else:
                # Anonymous access
                ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        request.jwt = None
        request.user_id = None
        token = _extract_bearer_token(request)
        if token:
            try:
                claims = decode_token(token)
                if claims.get("type") == "access":
                    request.jwt = claims
                    request.user_id = claims.get("sub")
            except jwt.InvalidTokenError:
                # Ignore invalid token for public routes
                pass
        return view_func(request, *args, **kwargs)
    return wrapper
