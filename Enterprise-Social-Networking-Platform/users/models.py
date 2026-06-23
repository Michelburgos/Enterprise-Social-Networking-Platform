"""
users/models.py
---------------
Define el modelo de usuario personalizado que extiende AbstractUser de Django.
Agrega campos de perfil (bio, avatar, departamento, cargo) y una relación
many-to-many asimétrica para seguir/ser seguido entre usuarios.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario personalizado del sistema.

    Extiende AbstractUser para reemplazar el campo de login por email
    y añadir información de perfil profesional y social.

    Campos heredados relevantes de AbstractUser:
        username, first_name, last_name, password, is_active, date_joined, etc.

    Atributos:
        email (EmailField): Dirección de correo única; se usa como USERNAME_FIELD.
        bio (TextField): Texto libre de presentación. Máx. 500 caracteres.
        avatar (ImageField): Foto de perfil; se guarda en media/avatars/.
        department (CharField): Área o departamento en la organización.
        position (CharField): Cargo o título profesional.
        following (ManyToManyField → self): Usuarios a los que sigue este usuario.
            - symmetrical=False: A sigue a B no implica que B siga a A.
            - related_name="followers": desde cualquier usuario se puede hacer
              user.followers.all() para obtener quiénes le siguen.
    """

    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)

    # Relación de seguimiento: muchos a muchos sobre sí mismo (self-referential)
    following = models.ManyToManyField(
        "self",                    # Referencia al propio modelo User
        symmetrical=False,         # La relación NO es recíproca automáticamente
        related_name="followers",  # Nombre inverso: user.followers.all()
        blank=True,
    )

    # El campo que Django usa para autenticar (en lugar del username por defecto)
    USERNAME_FIELD = "email"

    # Campos requeridos al crear un superusuario por consola (además de email y password)
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    # ------------------------------------------------------------------
    # Propiedades calculadas (no se almacenan en DB)
    # ------------------------------------------------------------------

    @property
    def followers_count(self):
        """Retorna el número de usuarios que siguen a este usuario."""
        return self.followers.count()

    @property
    def following_count(self):
        """Retorna el número de usuarios a los que este usuario sigue."""
        return self.following.count()
    

    
