from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Notification.

    Convierte instancias de Notification a formato JSON y viceversa.
    Incluye campos adicionales derivados del usuario remitente (sender).

    Campos adicionales (read-only):
        sender_name (str): Nombre completo del remitente, obtenido
            mediante `get_full_name()`.
        sender_username (str): Nombre de usuario del remitente.
    """

    sender_name = serializers.CharField(
        source="sender.get_full_name",
        read_only=True
    )
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender_name",
            "sender_username",
            "notification_type",
            "post",
            "created_at",
            "is_read",
        ]


class NotificationListView(generics.ListAPIView):
    """
    Vista de solo lectura que retorna la lista de notificaciones
    del usuario autenticado.

    - Método HTTP: GET
    - Autenticación: Requerida (IsAuthenticated)
    - Endpoint sugerido: /api/notifications/

    Optimiza las consultas a la base de datos usando `select_related`
    para traer en un solo query los datos del remitente y la
    publicación asociada.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna las notificaciones dirigidas al usuario que
        realiza la solicitud, ordenadas por defecto según
        el Meta del modelo.

        Returns:
            QuerySet: Notificaciones filtradas por `recipient`,
            con `sender` y `post` precargados mediante JOIN.
        """
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related("sender", "post")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """
    Marca todas las notificaciones no leídas del usuario
    autenticado como leídas en una sola operación en la BD.

    - Método HTTP: POST
    - Autenticación: Requerida (IsAuthenticated)
    - Endpoint sugerido: /api/notifications/mark-all-read/

    Args:
        request (Request): Objeto de solicitud DRF. Se usa
            `request.user` para filtrar las notificaciones.

    Returns:
        Response (200 OK): JSON con mensaje de confirmación.
            Ejemplo: {"detail": "Notificaciones marcadas como leidas"}
    """
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return Response({"detail": "Notificaciones marcadas como leidas"})


def notifications_view(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post')
    return render(request, 'notifications.html', {'notifications': notifications})


