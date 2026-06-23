"""
users/views.py
--------------
Vistas de la API para gestión de usuarios: registro, perfil, búsqueda
y toggle de seguimiento (follow/unfollow).

Endpoints expuestos (ver users/urls.py):
    POST   /api/users/register/          → RegistroView
    POST   /api/users/login/             → TokenObtainPairView (simplejwt, en urls.py)
    GET    /api/users/me/                → ProfileView
    PATCH  /api/users/me/                → ProfileView
    GET    /api/users/                   → UserListView
    GET    /api/users/<username>/        → UserDetailView
    POST   /api/users/<username>/follow/ → follow_toggle
"""

from django.shortcuts import render, redirect
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model


from .serializers import RegistroSerializer, UserProfileSerializer, UserMinimalSerializer


User = get_user_model()


class RegistroView(generics.CreateAPIView):
    """
    Crea una nueva cuenta de usuario.

    Método:  POST
    URL:     /api/users/register/
    Auth:    No requerida (AllowAny).
    Body:    { email, username, first_name, last_name, password, password2 }
    Retorna: 201 con los datos del usuario creado (sin contraseña).
    """

    queryset = User.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Consulta o actualiza el perfil del usuario autenticado.

    Métodos: GET (consultar), PUT / PATCH (actualizar parcialmente)
    URL:     /api/users/me/
    Auth:    JWT requerido.

    get_object() retorna siempre el usuario del request, no necesita pk ni username.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retorna el usuario autenticado como objeto a serializar."""
        return self.request.user


class UserDetailView(generics.RetrieveAPIView):
    """
    Consulta el perfil público de cualquier usuario por su username.

    Método:  GET
    URL:     /api/users/<username>/
    Auth:    JWT requerido.
    Retorna: Perfil completo incluyendo is_following según quien consulta.
    """

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "username"   # DRF busca el objeto por User.username


class UserListView(generics.ListAPIView):
    """
    Lista todos los usuarios excepto el autenticado. Soporta búsqueda por nombre.

    Método:     GET
    URL:        /api/users/?q=<término>
    Auth:       JWT requerido.
    Query param 'q': filtra por username que contenga el término (case-insensitive).
    Retorna:    Lista de usuarios con is_following para mostrar estado correcto en UI.
    """

    serializer_class = UserProfileSerializer  
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Excluye al usuario actual y filtra por búsqueda opcional.
        """
        qs = User.objects.exclude(pk=self.request.user.pk)
        query = self.request.query_params.get("q", "")

        if query:
            qs = qs.filter(username__icontains=query)

        return qs.order_by("first_name")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def follow_toggle(request, username):
    """
    Alterna el seguimiento del usuario autenticado hacia el usuario <username>.

    Método:  POST
    URL:     /api/users/<username>/follow/
    Auth:    JWT requerido.

    Lógica:
        - Si ya lo sigue  → lo deja de seguir (following=False).
        - Si no lo sigue  → empieza a seguirlo (following=True).
        - No se puede seguir a uno mismo → 400.

    Retorna:
        { "following": true/false }


    """
    try:
        target = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Usuario no encontrado"}, status=404)

    if target == request.user:
        return Response({"detail": "No puedes seguirte a ti mismo"}, status=400)

    if request.user.following.filter(pk=target.pk).exists():
        # Ya lo sigue → unfollow
        request.user.following.remove(target)
        following = False
    else:
        # No lo sigue → follow
        request.user.following.add(target)
        following = True

    return Response({"following": following})


from django.contrib.auth import authenticate, login as auth_login

def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    error = None
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            auth_login(request, user)
            return redirect('feed')
        error = 'Correo o contraseña incorrectos'

    return render(request, 'login.html', {'error': error})