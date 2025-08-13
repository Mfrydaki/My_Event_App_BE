# my_events_backend/auth.py
import os, time, jwt
from functools import wraps
from django.http import JsonResponse

JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-in-prod")
JWT_ALG = "HS256"
ACCESS_MIN = int(os.environ.get("JWT_ACCESS_MINUTES", "30"))

def make_access_token(user_id: str, email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email.lower(),
        "iat": now,
        "exp": now + ACCESS_MIN * 60,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def require_jwt(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Bearer "):
            return JsonResponse({"error": "Missing Bearer token"}, status=401)
        token = auth[len("Bearer "):].strip()
        try:
            claims = decode_token(token)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)
        request.jwt = claims
        return view_func(request, *args, **kwargs)
    return wrapper
