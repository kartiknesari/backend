from rest_framework import viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserSerializer,
    UserSignupSerializer,
    CustomTokenObtainPairSerializer,
)
from .models import CustomUser


class CustomDjangoModelPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()

    permission_classes = [CustomDjangoModelPermissions]
    authentication_classes = [JWTAuthentication]

    serializer_class = UserSerializer

    def get_serializer_class(self):  # type: ignore
        if self.action == "create":
            return UserSignupSerializer
        return UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
