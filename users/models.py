from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Fields inherited from AbstractUser include:
        - username
        - first_name
        - last_name
        - password
        - is_active, is_staff, is_superuser
        - date_joined, last_login

    Custom fields added:
        email (unique): User's email address, must be unique across all users.
        date_of_birth: Optional field storing the user's date of birth.

    Returns a string representation of the user.
     By default, it returns the username.
    """
    email = models.EmailField(unique=True)
    date_of_birth = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username