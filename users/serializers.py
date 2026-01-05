from datetime import date, datetime, timedelta
from email.message import EmailMessage

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
import logging
from django.core.mail import send_mail
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import (
    validate_password as validate_password_strength,
)

from .models import CustomUser


logger = logging.getLogger(__name__)


class UserSignupSerializer(serializers.ModelSerializer):
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
            "date_joined",
            "role",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "date_joined": {"required": True},
        }

    def validate_email(self, value):
        # Normalize email to lowercase
        return value.lower()

    def validate_dob(self, value):
        if value:
            # Ensure 'value' is a date object, which it should be from a DateField
            # Calculate age based on today's date
            today = date.today()
            age = (
                today.year
                - value.year
                - ((today.month, today.day) < (value.month, value.day))
            )
            if age < 18:
                raise serializers.ValidationError(
                    f"Invalid Date of Birth. User must be at least 18 years old."
                )
            return value

    def validate_role(self, value):
        # Ensure role is valid
        valid_roles = [choice[0] for choice in CustomUser.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Choose from {valid_roles}"
            )
        return value

    def create(self, validated_data):
        try:
            # Use the custom manager's `create_user` method for atomic user creation
            password = CustomUser.objects.make_random_password()
            email = validated_data.pop("email")
            user = CustomUser.objects.create_user(
                email=email, password=password, **validated_data
            )

            # --- Send Welcome Email with Temporary Password and Reset Link (handled gracefully) ---
            try:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = (
                    f"{settings.CLIENT_URL}/auth/set-initial-password/{uid}/{token}/"
                )

                subject = "Welcome to the HR App - Set Your Password"
                message = (
                    f"Hello {user.first_name},\n\n"
                    "An account has been created for you on the HR App.\n\n"
                    f"Your temporary password is: {password}\n\n"
                    "Please set your permanent password by clicking the link below:\n"
                    f"{reset_url}\n\n"
                    "Thank you,\n"
                    "The HR App Team"
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,  # Keep False to ensure errors are raised here and caught by our inner try-except
                )
            except Exception as email_exc:
                logger.error(
                    f"Failed to send welcome email to {user.email}: {email_exc}"
                )

            return user
        except IntegrityError as e:
            if "email" in str(e).lower():
                raise serializers.ValidationError(
                    {"email": "This email is already registered"}
                )
            raise serializers.ValidationError(
                {"error": "Failed to create user due to database error."}
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during user signup: {e}")
            raise serializers.ValidationError(
                {"error": "An unexpected error occurred during user creation."}
            )


class InitialPasswordSetSerializer(serializers.Serializer):
    id = serializers.CharField(write_only=True)
    access = serializers.CharField(write_only=True)
    temp_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
    )
    new_password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        required=True,
        min_length=8,
        validators=[validate_password_strength],
    )
    new_password_confirm = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
    )

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs.get("id")))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError({"id": "Invalid user ID."})

        if not default_token_generator.check_token(user, attrs.get("access")):
            raise serializers.ValidationError({"access": "Invalid or expired token."})

        if not user.check_password(attrs.get("temp_password")):
            raise serializers.ValidationError(
                {"temp_password": "Incorrect temporary password."}
            )

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Password fields do not match."}
            )

        attrs["user"] = user
        return attrs


# Set new password
class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
    )
    new_password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        required=True,
        min_length=8,
        validators=[validate_password_strength],
    )
    new_password_confirm = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
    )

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect current password.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Password fields do not match."}
            )
        return attrs


class SetPasswordResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class DateOnlyField(serializers.DateField):
    def to_representation(self, value):
        if isinstance(value, datetime):
            return value.date()
        return super().to_representation(value)


# Email
class EmailCheckRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class EmailCheckResponseSerializer(serializers.Serializer):
    exists = serializers.BooleanField()
    message = serializers.CharField()


# Error
class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    code = serializers.IntegerField(required=False)
    message = serializers.CharField()


# User
class UserSerializer(serializers.ModelSerializer):
    dob = DateOnlyField(required=False, allow_null=True)
    date_joined = DateOnlyField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "dob",
            "date_joined",
            "role",
            "is_superuser",
            "is_staff",
            "user_permissions",
            "is_active",
            "is_temp_password",
        ]


# Auth
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["id"] = str(self.user.id)
        data["email"] = self.user.email
        data["first_name"] = self.user.first_name
        data["last_name"] = self.user.last_name
        data["is_temp_password"] = self.user.is_temp_password

        if self.user.is_temp_password:
            raise serializers.ValidationError(
                "Please set password again. Check your inbox for further instructions from '@hrapp.com'"
            )
        return data
