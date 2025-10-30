from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("candidate", "Candidate"),
        ("manager", "Recruiter"),
        ("sme", "Subject Matter Expert"),
        ("administrator", "administrator"),
    ]
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    middle_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True, blank=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    access_level = models.IntegerField(
        choices=[
            (0, "User"),
            (1, "Manager"),
            (2, "Administrator"),
        ],
        default=0,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role", "access_level"]

    def save(self, *args, **kwargs):
        self.email = self.email.lower()  # Normalize email
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.email
