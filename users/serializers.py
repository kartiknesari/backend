from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(min_length=2)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "dob",
            "password",
            "role",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    def validate_email(self, value):
        # Normalize email to lowercase
        return value.lower()

    def validate_role(self, value):
        # Ensure role is valid
        valid_roles = [choice[0] for choice in CustomUser.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Choose from {valid_roles}"
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        try:
            user = CustomUser.objects.create(**validated_data)
            user.set_password(password)
            user.save()
            return user
        except IntegrityError as e:
            if "email" in str(e).lower():
                raise serializers.ValidationError(
                    {"email": "This email is already registered"}
                )
            raise serializers.ValidationError(
                {"error": "Failed to create user due to database error"}
            )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "dob",
            "role",
            "is_superuser",
            "is_staff",
            "user_permissions",
            "date_joined",
            "is_active",
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["id"] = str(self.user.id)
        data["email"] = self.user.email
        data["first_name"] = self.user.first_name
        data["last_name"] = self.user.last_name
        return data
