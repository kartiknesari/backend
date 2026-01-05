import datetime
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.crypto import get_random_string
import uuid


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "administrator")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def make_random_password(
        self,
        length=10,
        allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789",
    ):
        """
        Generate a random password with the given length and allowed characters.
        The default value of allowed_chars does not have "I" or "O" or "l" or
        "0" or "1", to avoid confusion between similar characters.
        """
        return get_random_string(length, allowed_chars)


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("data_entry", "Data Entry Operator"),
        ("manager", "Manager"),
        ("instructor", "Instructor"),
        ("administrator", "Administrator"),
    ]

    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    middle_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True, blank=False)
    dob = models.DateField(null=True, blank=True)
    date_joined = models.DateField(default=datetime.date.today)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="candidate")
    is_temp_password = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()  # type: ignore

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()  # Normalize email

        if self.role == "administrator":
            self.is_staff = True
            self.is_superuser = True

        super().save(*args, **kwargs)

        # Assign group
        if self.role:
            group, _ = Group.objects.get_or_create(name=self.role)
            self.groups.add(group)

    class Meta:
        indexes = [
            models.Index(fields=["email", "id"]),
        ]

    def __str__(self):
        return self.email
