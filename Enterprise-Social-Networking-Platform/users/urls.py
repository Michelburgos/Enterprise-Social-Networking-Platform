from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from . import views
 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("register/",      views.RegistroView.as_view(),  name="api-register"),
    path("login/",         TokenObtainPairView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(),    name="token-refresh"),
    path("me/",                    views.ProfileView.as_view(),    name="api-profile"),
    path("",                       views.UserListView.as_view(),   name="user-list"),
    path("<str:username>/",        views.UserDetailView.as_view(), name="user-detail"),
    path("<str:username>/follow/", views.follow_toggle,            name="follow-toggle"),
]