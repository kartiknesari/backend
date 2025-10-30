from django.db import IntegrityError
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import CustomUser


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(min_length=2)

    class Meta:
        model = CustomUser
        fields = [
            "user_id",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "password",
            "role",
            "access_level",
        ]
        extra_kwargs = {
            "user_id": {"read_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "role": {"required": True},
            "access_level": {"required": True},
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


class UserSigninSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        if not email or not password:
            raise serializers.ValidationError(
                {"non_field_errors": ["Email and password are required."]}
            )
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                {"non_field_errors": ["Request context is missing."]}
            )
        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )
        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password."]}
            )
        attrs["user"] = user
        return attrs
