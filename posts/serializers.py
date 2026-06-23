"""
posts/serializers.py
--------------------
Serializers del módulo de posts. Convierten instancias de Post y Comment
hacia/desde JSON e incluyen datos anidados del autor.

Dependencias:
    UserMinimalSerializer (users.serializers) → embebido en author.
"""

from rest_framework import serializers
from .models import Post, Like, Comment
from users.serializers import UserMinimalSerializer


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios de un post.

    El campo 'author' se expande con UserMinimalSerializer (read_only)
    para mostrar nombre, avatar y cargo del autor sin permitir su edición.


    """

    # Anida los datos del autor en lugar de mostrar solo el ID
    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer completo para publicaciones.

    Campos calculados (no almacenados en DB):
        likes_count    → propiedad del modelo Post.
        comments_count → propiedad del modelo Post.
        is_liked       → True si el usuario autenticado ya dio like a este post.

    El autor se muestra anidado con datos mínimos (UserMinimalSerializer).

    """

    author = UserMinimalSerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    # SerializerMethodField invoca get_is_liked(self, obj) automáticamente
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "author", "content", "image",
            "likes_count", "comments_count", "is_liked",   
            "created_at", "updated_at",                    
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_is_liked(self, obj):
        """
        Retorna True si el usuario autenticado ya dio like a este post.

        Requiere context={'request': request} al instanciar el serializer.
        Si el usuario no está autenticado, retorna False.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

        
