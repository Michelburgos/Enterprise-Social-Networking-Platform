"""
users/serializers.py
--------------------
Serializers del módulo de usuarios. Transforman instancias de User
hacia/desde JSON y aplican validaciones de negocio (ej. contraseñas iguales).

Jerarquía de uso:
    RegistroSerializer      → POST /api/users/register/
    UserProfileSerializer   → GET/PATCH /api/users/me/ y GET /api/users/<username>/
    UserMinimalSerializer   → Embebido en PostSerializer y CommentSerializer
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas cuentas de usuario.

    Campos extra (no en el modelo):
        password  (write_only): Contraseña principal. Mín. 8 caracteres.
        password2 (write_only): Confirmación de contraseña. No se guarda.

    Validaciones:
        - password == password2 (validate).

    Al crear:
        - Se elimina password2 del diccionario validado.
        - Se usa create_user() para hashear la contraseña correctamente.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password", "password2"]

    def validate(self, data):
        """Verifica que ambas contraseñas sean idénticas."""
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        """
        Crea el usuario con contraseña hasheada.
        password2 se descarta antes de llamar a create_user().
        """
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer completo del perfil de un usuario.

    Usado para ver y editar el perfil propio (GET/PATCH /api/users/me/)
    y para consultar el perfil de otro usuario (GET /api/users/<username>/).

    Campos de solo lectura calculados:
        followers_count  → propiedad del modelo.
        following_count  → propiedad del modelo.
        is_following     → calculado con get_is_following() según el usuario autenticado.


    """

    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
    # SerializerMethodField llama automáticamente a get_is_following(self, obj)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "bio", "avatar", "department", "position",
            "followers_count", "following_count", "is_following",
            "date_joined",      
        ]
        read_only_fields = ["id", "date_joined", "email"]

    def get_is_following(self, obj):
        """
        Retorna True si el usuario autenticado sigue al usuario 'obj'.

        Requiere que el serializer se instancie con context={'request': request}
        para poder acceder al usuario autenticado.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.following.filter(pk=obj.pk).exists()
        return False


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer reducido para embeber datos de usuario en otros recursos.

    Se usa dentro de PostSerializer y CommentSerializer para mostrar
    información básica del autor sin exponer datos sensibles.
    """

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "avatar", "position"]


        