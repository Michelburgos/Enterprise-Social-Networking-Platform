"""
notifications/models.py
-----------------------
Define el modelo Notification que registra eventos sociales relevantes
para un usuario: likes, comentarios y nuevos seguidores.
Los registros se crean automáticamente mediante signals (ver signals.py).
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Notificación de actividad social enviada a un usuario (recipient).

    Se genera automáticamente desde signals cuando:
      - Alguien da like a un post del recipient.
      - Alguien comenta un post del recipient.
      - Alguien empieza a seguir al recipient (no implementado aún en signals).

    Atributos:
        recipient (FK → User): Usuario que RECIBE la notificación.
        sender (FK → User): Usuario que GENERÓ la acción (like, comentario, follow).
        notification_type (CharField): Tipo de evento; debe ser uno de TYPE.
        post (FK → Post | null): Post relacionado (solo para like y comentario).
            Puede ser nulo si la notificación es de tipo "follow".
        is_read (BooleanField): False hasta que el usuario la marque como leída.
        created_at (DateTimeField): Fecha/hora de creación (automática).

    Tipos disponibles (TYPE):
        "like"        → Alguien dio like al post del recipient.
        "Comentario"  → Alguien comentó el post del recipient.
        "follow"      → Alguien empezó a seguir al recipient.

    """

    # Opciones válidas para notification_type
    TYPE = [
        ("like",        "Like en tu post"),
        ("comentario",  "Comentario en tu post"),
        ("follow",      "Alguien te siguió"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",       # user.notifications.all()
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",  # user.sent_notifications.all()
    )
    notification_type = models.CharField(max_length=20, choices=TYPE)

    # FK a Post en otra app; se referencia como string para evitar importación circular
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        null=True,          # Permite notificaciones sin post (ej. follow)
        blank=True,
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # Notificaciones más recientes primero





