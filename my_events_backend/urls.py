
from django.contrib import admin
from django.urls import path
from events.views import events_view, event_detail_view
from users.views import register_view, login_view, profile_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # events
    path("events/", events_view, name="events"),
    path("events/<str:event_id>/", event_detail_view, name="event-detail"),
    
    # auth/users (PyMongo)
    path("auth/register/", register_view, name="register"),
    path("auth/login/", login_view, name="login"),
    path("auth/profile/", profile_view, name="profile"),
]
