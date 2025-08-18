import os
import time
import jwt
from functools import wraps
from django.http import JsonResponse
from django.http import HttpRequest

# Configuration
SECRET: str = os.environ.get("JWT_SECRET", "my-secret")
ALGORITHM: str = "HS256"
LIFETIME_MINUTES: int = 30  # Token lifetime in minutes


def make_access_token(user_id: str, email: str) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    user_id : str
    Unique identifier of the user (usually a MongoDB _id as string).
    email : str
    The user's email address.

    Returns
    -------
    str
    Encoded JWT token string.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,                      # subject (who the token is for)
        "email": (email or "").lower(),      # normalized email
        "iat": now,                           # issued at (unix seconds)
        "exp": now + LIFETIME_MINUTES * 60,   # expiration (unix seconds)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Parameters
    ----------
    token : str
    The encoded JWT string.

    Returns
    -------
    dict
    The decoded payload (claims).

    Raises
    ------
    jwt.ExpiredSignatureError
    If the token has expired.
    jwt.InvalidTokenError
    If the token is invalid or has a bad signature.
    """
    return jwt.decode(token, SECRET, algorithms=[ALGORITHM])


def _get_token_from_request(request: HttpRequest) -> str | None:
    """
    Extract a Bearer token from the Authorization header.

    Expected Header
    ---------------
    Authorization: Bearer <token>

    Parameters
    ----------
    request : HttpRequest
    The Django request object.

    Returns
    -------
    str | None
    The token string if present, otherwise None.
    """
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def require_jwt(view_func):
    """
    Require a valid JWT token.

    Behavior
    --------
    - Returns HTTP 401 if the token is missing, expired, or invalid.
    - On success, sets `request.user_id` and `request.user_email` from claims.

    Parameters
    ----------
    view_func : callable
    The Django view function to wrap.

    Returns
    -------
    callable
    Wrapped view function that enforces JWT authentication.
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        token = _get_token_from_request(request)
        if not token:
            return JsonResponse({"error": "Missing Bearer token"}, status=401)

        try:
            claims = decode_token(token)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)

        request.user_id = claims.get("sub")
        request.user_email = claims.get("email")
        return view_func(request, *args, **kwargs)

    return wrapper


def optional_jwt(view_func):
    """
    Optionally accept a JWT token.

    Behavior
    --------
    - If a valid Bearer token is provided, sets "request.user_id" and "request.user_email" from claims.
    - If there is no token or it is invalid/expired, continues anonymously.

    Parameters
    ----------
    view_func : callable
    The Django view function to wrap.

    Returns
    -------
    callable
    Wrapped view function that reads JWT when available.
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        request.user_id = None
        request.user_email = None

        token = _get_token_from_request(request)
        if token:
            try:
                claims = decode_token(token)
                request.user_id = claims.get("sub")
                request.user_email = claims.get("email")
            except jwt.InvalidTokenError:
                # Ignore invalid/expired token for public routes
                pass

        return view_func(request, *args, **kwargs)

    return wrapper
