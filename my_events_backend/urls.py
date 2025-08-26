from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Users authentication routes
    path("auth/", include("users.urls")),

    # Events routes
    path("events/", include("events.urls")),

    #User's actions(attending)
    path("api/users/", include("users.urls")),

]