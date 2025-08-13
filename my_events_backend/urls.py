"""
URL configuration for my_events_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from events.views import events_view, event_detail_view
from users.views import register_view, login_view, me_view

urlpatterns = [
    path("admin/", admin.site.urls),
    # events
    path("events/", events_view, name="events"),
    path("events/<str:event_id>/", event_detail_view, name="event-detail"),
    # auth/users (PyMongo)
    path("auth/register/", register_view, name="register"),
    path("auth/login/", login_view, name="login"),
    path("auth/me/", me_view, name="me"),
]
