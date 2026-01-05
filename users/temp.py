import logging
import smtplib
import socket
from django.apps import AppConfig
from django.conf import settings


class UsersAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Users"


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        post_migrate.connect(create_role_groups, sender=self)
        # Only run this check if the EMAIL_BACKEND is SMTP
        if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
            logger.info("Attempting to connect to email server during startup...")
            try:
                # Attempt to establish a connection to the SMTP server
                # Use a timeout to prevent hanging if the server is unreachable
                with smtplib.SMTP(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5
                ) as server:
                    server.noop()  # Send a NOOP command to test the connection
                logger.info(
                    f"Successfully connected to email server at {settings.EMAIL_HOST}:{settings.EMAIL_PORT}"
                )
            except (
                smtplib.SMTPConnectError,
                ConnectionRefusedError,
                socket.gaierror,  # Catches "Name or service not known"
                TimeoutError,
                OSError,
            ) as e:
                logger.error(
                    f"Failed to connect to email server at {settings.EMAIL_HOST}:{settings.EMAIL_PORT}. Error: {e}. Please ensure the email server is running and accessible."
                )
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during email server connection check: {e}"
                )
        else:
            logger.info(
                f"Email backend is not SMTP ({settings.EMAIL_BACKEND}), skipping connection check."
            )
