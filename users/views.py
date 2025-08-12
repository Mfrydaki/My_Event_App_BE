from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer
from .models import User

class RegisterView(APIView):
    """
    View for registering a new user.
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Calls create() from the serializer
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    """
    View for user login using email and password.
    Returns JWT tokens if credentials are correct.
    """
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Since we use email as USERNAME_FIELD
        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })
    class ProfileView(APIView):
        """
        View to retrieve the logged-in user's profile data.
        Requires authentication.
        """
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request):
         serializer = UserSerializer(request.user)
         return Response(serializer.data)

