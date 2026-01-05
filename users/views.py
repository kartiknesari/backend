from rest_framework import viewsets, permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from .serializers import (
    ErrorSerializer,
    EmailCheckRequestSerializer,
    EmailCheckResponseSerializer,
    ErrorSerializer,
    SetPasswordResponseSerializer,
    UserSerializer,
    UserSignupSerializer,
    SetPasswordSerializer,
    InitialPasswordSetSerializer,
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

    @extend_schema(responses={200: EmailCheckResponseSerializer, 400: ErrorSerializer})
    @action(
        methods=["post"],
        detail=False,
        url_path="check-email",
    )
    def check_email(self, request: Request):
        email = request.data.get("email", "").lower().strip()

        if not email:
            return ValidationError(
                {"message": "Email is required"}, code=status.HTTP_400_BAD_REQUEST
            )
        exists = self.queryset.filter(email=email).exists()

        return Response(
            {
                "exists": exists,
                "message": (
                    "User with this email already exists"
                    if exists
                    else "Email available"
                ),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={200: SetPasswordResponseSerializer, 400: ErrorSerializer},
        request=SetPasswordSerializer,
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="set-password",
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_password(self, request: Request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Set the new password and mark it as permanent
        user.set_password(serializer.validated_data["new_password"])
        user.is_temp_password = False
        user.save(update_fields=["password", "is_temp_password"])

        return Response({"message": "Password updated successfully."})

    @extend_schema(
        request=InitialPasswordSetSerializer,
        responses={200: SetPasswordResponseSerializer, 400: ErrorSerializer},
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="set-initial-password",
        permission_classes=[permissions.AllowAny],
    )
    def set_initial_password(self, request: Request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Set the new password and mark it as permanent
        user.set_password(serializer.validated_data["new_password"])
        user.is_temp_password = False
        user.save(update_fields=["password", "is_temp_password"])

        return Response({"message": "Password has been reset successfully."})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_active:
            raise ValidationError(
                {"message": "Active Employee cannot be removed."},
                code=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):  # type: ignore
        if self.action == "check_email":
            return EmailCheckRequestSerializer
        if self.action == "create" or self.action == "signup":
            return UserSignupSerializer
        if self.action == "set_password":
            return SetPasswordSerializer
        if self.action == "set_initial_password":
            return InitialPasswordSetSerializer
        return UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
