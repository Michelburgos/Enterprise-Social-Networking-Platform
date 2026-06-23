"""
posts/views.py
--------------
Vistas de la API para el módulo de publicaciones: feed personalizado,
CRUD de posts, toggle de like y listado/creación de comentarios.

Endpoints expuestos (ver posts/urls.py):
    GET    /api/posts/feed/              → FeedView
    GET    /api/posts/                   → PostListCreateView
    POST   /api/posts/                   → PostListCreateView
    GET    /api/posts/<pk>/              → PostDetailView
    PUT    /api/posts/<pk>/              → PostDetailView
    PATCH  /api/posts/<pk>/              → PostDetailView
    DELETE /api/posts/<pk>/              → PostDetailView
    POST   /api/posts/<pk>/like/         → like_toggle
    GET    /api/posts/<pk>/comments/     → CommentListCreateView
    POST   /api/posts/<pk>/comments/     → CommentListCreateView
"""

from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache

from .models import Post, Like, Comment
from .serializers import PostSerializer, CommentSerializer
from django.shortcuts import render, get_object_or_404


# Tiempo en segundos que el feed de un usuario puede estar cacheado
FEED_CACHE = 300  # 5 minutos


class FeedView(generics.ListAPIView):
    """
    Retorna el feed personalizado del usuario autenticado.

    Muestra los posts propios más los de los usuarios que sigue,
    ordenados del más reciente al más antiguo (definido en Post.Meta).

    Método:  GET
    URL:     /api/posts/feed/
    Auth:    JWT requerido.

    Optimización:
        prefetch_related("likes", "comments") evita N+1 queries al calcular
        likes_count y comments_count por cada post.

    """

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Obtiene los IDs de los usuarios que sigue + el propio ID
        following_ids = list(user.following.values_list("id", flat=True))
        following_ids.append(user.id)

        return (
            Post.objects.filter(author_id__in=following_ids)  
            .prefetch_related("likes", "comments")
        )


class PostListCreateView(generics.ListCreateAPIView):
    """
    Lista todos los posts o crea uno nuevo.

    Métodos:
        GET  → Lista paginada de todos los posts.
        POST → Crea un post nuevo asignando el usuario autenticado como autor.

    URL:  /api/posts/
    Auth: JWT requerido.

    Al crear un post:
        - Se invalida el caché del feed del autor y de todos sus seguidores,
          para que vean el post nuevo en su próxima petición.

    Optimización:
        select_related("author") → JOIN con User en una sola query.
        prefetch_related("likes", "comments") → evita N+1 en propiedades calculadas.
    """

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Post.objects.select_related("author").prefetch_related("likes", "comments")
        author_username = self.request.query_params.get("author", None)
        if author_username:
            qs = qs.filter(author__username=author_username)
        return qs

    def perform_create(self, serializer):
        """
        Guarda el post con el autor actual e invalida cachés de feed afectados.
        """
        post = serializer.save(author=self.request.user)

        # Invalida el caché del feed de cada seguidor del autor
        for follower in self.request.user.followers.all():
            cache.delete(f"feed_{follower.pk}")

        # Invalida también el feed del propio autor
        cache.delete(f"feed_{self.request.user.pk}")


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Consulta, actualiza o elimina un post específico por su ID (pk).

    Métodos:
        GET    → Ver el post.
        PUT    → Reemplazar completamente el post (solo el autor).
        PATCH  → Actualizar campos parcialmente (solo el autor).
        DELETE → Eliminar el post (solo el autor).

    URL:  /api/posts/<pk>/
    Auth: JWT requerido.

    """

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.select_related("author")

    def perform_update(self, serializer):
        """Solo el autor puede editar su post."""
        if self.get_object().author != self.request.user:
            raise PermissionDenied("No puedes editar este post")
        serializer.save()

    def perform_destroy(self, instance):
        """Solo el autor puede eliminar su post."""
        if instance.author != self.request.user:
            raise PermissionDenied("No puedes eliminar este post")
        instance.delete()


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def like_toggle(request, pk):
    """
    Alterna el like del usuario autenticado en el post con id=<pk>.

    Método:  POST
    URL:     /api/posts/<pk>/like/
    Auth:    JWT requerido.

    Lógica (toggle idempotente):
        - Si NO existe el like → lo crea (liked=True).
        - Si YA existe el like → lo elimina (liked=False).

    Retorna:
        { "liked": true/false, "likes_count": <int> }

    Efecto secundario:
        Al crear un Like, el signal notify_like (signals.py) crea
        automáticamente una Notification para el autor del post.
    """
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({"detail": "Post no encontrado"}, status=404)

    # get_or_create retorna (instancia, fue_creado)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        # El like ya existía → se elimina (unlike)
        like.delete()
        liked = False
    else:
        # El like no existía → se creó (like)
        liked = True

    return Response({"liked": liked, "likes_count": post.likes_count})


class CommentListCreateView(generics.ListCreateAPIView):
    """
    Lista los comentarios de un post o agrega uno nuevo.

    Métodos:
        GET  → Lista todos los comentarios del post <pk>.
        POST → Crea un comentario nuevo en el post <pk>.

    URL:  /api/posts/<pk>/comments/
    Auth: JWT requerido.

    El pk del post se obtiene de kwargs (parte de la URL), no del body.

    Efecto secundario:
        Al guardar un Comment, el signal notify_comment (signals.py) crea
        automáticamente una Notification para el autor del post.

    """

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra comentarios por el post indicado en la URL."""
        return Comment.objects.filter(
            post_id=self.kwargs["pk"]
        ).select_related("author")

    def perform_create(self, serializer):
        """
        Guarda el comentario asignando el autor y el post automáticamente.
        El cliente solo envía 'content' en el body.
        """
        post = Post.objects.get(pk=self.kwargs["pk"])
        serializer.save(author=self.request.user, post=post)


def post_detail_view(request, pk):
    post = get_object_or_404(Post.objects.prefetch_related('comments__author', 'likes'), pk=pk)
    comments = post.comments.select_related('author').all()
    return render(request, 'post_detail.html', {'post': post, 'comments': comments})