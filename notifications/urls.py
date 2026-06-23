from django.urls import path
from . import views
 
urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("read-all/", views.mark_all_read, name="notification-read"),
    path("view/", views.notifications_view, name="notifications-template"),
]