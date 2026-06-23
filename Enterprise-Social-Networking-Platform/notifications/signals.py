"""
notifications/signals.py
------------------------
Signals de Django que crean notificaciones automáticamente cuando ocurren
eventos sociales: un like nuevo o un comentario nuevo en un post.

Cómo funciona:
    Django emite señales (signals) después de ciertos eventos del ORM.
    Con @receiver se "escucha" esa señal y se ejecuta la función decorada.
    Esto desacopla la lógica de notificaciones del código de views/serializers.

Registro de los signals:
    Para que Django cargue estos handlers, la clase NotificationsConfig
    (notifications/apps.py) debe importar este módulo en su método ready():

        class NotificationsConfig(AppConfig):
            def ready(self):
                import notifications.signals  # noqa

Signals implementados:
    notify_like     → post_save sobre Like
    notify_comment  → post_save sobre Comment

"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from posts.models import Like, Comment
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=Like)
def notify_like(sender, instance, created, **kwargs):
    """
    Crea una notificación de tipo "like" cuando se guarda un Like nuevo.

    Parámetros del signal (inyectados por Django):
        sender   (class Like): Clase que emitió la señal.
        instance (Like):       Instancia del Like recién guardado.
        created  (bool):       True si es INSERT, False si es UPDATE.
        **kwargs:              Argumentos adicionales del signal (raw, using, etc.).

    Condiciones para crear la notificación:
        1. created=True → solo en likes nuevos, no en actualizaciones.
        2. El usuario que da like NO es el autor del post (evita auto-notificarse).

    Resultado:
        Se crea un registro en Notification con:
            recipient = autor del post
            sender    = usuario que dio el like
            type      = "like"
            post      = post que recibió el like
    """
    if created and instance.user != instance.post.author:
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.user,
            notification_type="like",
            post=instance.post,
        )


@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    """
    Crea una notificación de tipo "Comentario" cuando se guarda un Comment nuevo.

    Parámetros del signal (inyectados por Django):
        sender   (class Comment): Clase que emitió la señal.
        instance (Comment):       Instancia del Comment recién guardado.
        created  (bool):          True si es INSERT, False si es UPDATE.
        **kwargs:                 Argumentos adicionales del signal.

    Condiciones para crear la notificación:
        1. created=True → solo en comentarios nuevos, no en ediciones.
        2. El autor del comentario NO es el autor del post.

    Resultado:
        Se crea un registro en Notification con:
            recipient = autor del post
            sender    = autor del comentario
            type      = "comentario"  
            post      = post comentado

    """
    if created and instance.author != instance.post.author:
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type="comentario",
            post=instance.post,
        )



@receiver(m2m_changed, sender=User.following.through)
def notify_follow(sender, instance, action, pk_set, **kwargs):
    """
    Crea una notificación cuando un usuario empieza a seguir a otro.

    Parámetros del signal:
        sender   → Modelo intermedio de la relación ManyToMany (through).
        instance → Usuario que realiza la acción (el que sigue).
        action   → Tipo de acción ('pre_add', 'post_add', etc.).
        pk_set   → IDs de los usuarios afectados (a quién sigue).
        **kwargs → Otros argumentos.

    Condiciones:
        - action == 'post_add' → Solo después de agregar el follow.
        - Evitar auto-follow (aunque normalmente no debería pasar).

    Resultado:
        Se crea una notificación con:
            recipient = usuario seguido
            sender    = usuario que sigue
            type      = "follow"
    """

    if action == "post_add":
        for user_id in pk_set:
            try:
                followed_user = User.objects.get(pk=user_id)

                # Evitar auto-follow
                if instance != followed_user:
                    Notification.objects.create(
                        recipient=followed_user,
                        sender=instance,
                        notification_type="follow",
                    )

            except User.DoesNotExist:
                continue