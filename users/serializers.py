
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading user data (safe output).
        
    This serializer is used to return user information in API responses,
    without exposing sensitive fields such as the password.
    """
    class Meta:
        model = User 
        fields = ["id", "email", "username", "first_name", "last_name", "date_of_birth"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user.
    
    Responsibilities:
    - Validates input data (email format, uniqueness, password strength).
    - Hashes the password before saving the user.
    - Creates a new user instance using Django's `create_user` method.
    """
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists")]
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "username", "password", "first_name", "last_name", "date_of_birth"]

    def validate_username(self, value):
     """
    Validate the username field.
    
    """   
     if " " in value:
        raise serializers.ValidationError("Username must not contain spaces.")
        return value
      
    def create(self, validated_data):
        """
        Create a new user instance.
        
        Uses the model manager's `create_user` method to ensure:
        - The password is hashed correctly.
        - Any additional model-specific setup is applied.
        """
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
       
