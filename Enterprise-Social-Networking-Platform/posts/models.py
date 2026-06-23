"""
posts/models.py
---------------
Define los modelos del feed social: publicaciones (Post), reacciones (Like)
y comentarios (Comment). Todos están vinculados al usuario a través de
settings.AUTH_USER_MODEL para respetar la configuración de usuario personalizado.
"""

from django.db import models
from django.conf import settings


class Post(models.Model):
    """
    Publicación creada por un usuario.

    Atributos:
        author (FK → User): Usuario que creó el post. Si se elimina el usuario,
            se eliminan en cascada todos sus posts.
        content (TextField): Texto principal del post. Máx. 3000 caracteres.
        image (ImageField): Imagen opcional adjunta; se guarda en media/posts/.
        created_at (DateTimeField): Fecha/hora de creación (automática, inmutable).
        updated_at (DateTimeField): Fecha/hora de última modificación (automática).

    Ordenamiento por defecto: más recientes primero (-created_at).
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,   # Borrar usuario → borra sus posts
        related_name="posts",       # user.posts.all()
    )
    content = models.TextField(max_length=3000)
    image = models.ImageField(upload_to="posts/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Solo al crear
    updated_at = models.DateTimeField(auto_now=True)      # En cada save()

    class Meta:
        ordering = ["-created_at"]  # Posts más nuevos primero

    # ------------------------------------------------------------------
    # Propiedades calculadas
    # ------------------------------------------------------------------

    @property
    def likes_count(self):
        """Retorna el total de likes que tiene este post."""
        return self.likes.count()

    @property
    def comments_count(self):
        """Retorna el total de comentarios de este post."""
        return self.comments.count()


class Like(models.Model):
    """
    Reacción 'me gusta' de un usuario sobre un post.

    La combinación (user, post) es única: un usuario solo puede dar
    un like por publicación. Si se intenta duplicar, la base de datos
    lanzará un IntegrityError.

    Atributos:
        user (FK → User): Usuario que dio el like.
        post (FK → Post): Post que recibió el like.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",   # user.likes.all()
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",   # post.likes.all()
    )

    class Meta:
        # Restricción de unicidad a nivel de base de datos
        unique_together = ("user", "post")


class Comment(models.Model):
    """
    Comentario escrito por un usuario sobre un post.

    Atributos:
        author (FK → User): Usuario que escribió el comentario.
        post (FK → Post): Post al que pertenece el comentario.
        content (TextField): Texto del comentario. Máx. 500 caracteres.
        created_at (DateTimeField): Fecha/hora de creación (automática).

    Ordenamiento por defecto: más recientes primero (-created_at).
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",    # user.comments.all()
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",    # post.comments.all()
    )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # Comentarios más nuevos primero

        
