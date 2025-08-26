from django.urls import path
from .views import register_view, login_view, profile_view, my_attending_events_view

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("profile/", profile_view, name="profile"),
    path("me/events/attending", my_attending_events_view, name="my-attending-events")
]
