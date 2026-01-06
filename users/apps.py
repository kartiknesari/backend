import logging
import smtplib
import socket
from django.conf import settings
from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

all_permissions = {
    "users": {
        "view": "users.view_customuser",
        "change": "users.change_customuser",
        "add": "users.add_customuser",
        "delete": "users.delete_customuser",
    },
    "questions": {
        # Questions
        "add_questions": "questions.add_question",
        "view_questions": "questions.view_question",
        "change_questions": "questions.change_question",
        "delete_questions": "questions.delete_question",
        # Topics
        "add_topics": "questions.add_topic",
        "view_topics": "questions.view_topic",
        "change_topics": "questions.change_topic",
        "delete_topics": "questions.delete_topic",
        # Domains
        "add_domains": "questions.add_domain",
        "view_domains": "questions.view_domain",
        "change_domains": "questions.change_domain",
        "delete_domains": "questions.delete_domain",
        # Case Payload
        "add_casepayload": "questions.add_casepayload",
        "view_casepayload": "questions.view_casepayload",
        "change_casepayload": "questions.change_casepayload",
        "delete_casepayload": "questions.delete_casepayload",
        # Diagram Payload
        "add_diagrampayload": "questions.add_diagrampayload",
        "view_diagrampayload": "questions.view_diagrampayload",
        "change_diagrampayload": "questions.change_diagrampayload",
        "delete_diagrampayload": "questions.delete_diagrampayload",
        # MCQ Payload
        "add_mcqpayload": "questions.add_mcqpayload",
        "view_mcqpayload": "questions.view_mcqpayload",
        "change_mcqpayload": "questions.change_mcqpayload",
        "delete_mcqpayload": "questions.delete_mcqpayload",
        # Numerical Payload
        "add_numericalpayload": "questions.add_numericalpayload",
        "view_numericalpayload": "questions.view_numericalpayload",
        "change_numericalpayload": "questions.change_numericalpayload",
        "delete_numericalpayload": "questions.delete_numericalpayload",
    },
}


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


# Move create_role_groups here, and its imports inside the function
def create_role_groups(sender, **kwargs):
    # Imports are moved inside the function to avoid AppRegistryNotReady error
    from django.contrib.auth.models import Group, Permission
    from users.models import CustomUser  # Use absolute import for clarity

    # 1. Define what each role is allowed to do
    # Format: 'app_label.codename'
    role_permissions = {
        "administrator": [
            *all_permissions["users"].values(),
            *all_permissions["questions"].values(),
        ],
        "manager": [*all_permissions["questions"].values()],
        "instructor": [],
        "data_entry": [],  # Usually no API permissions, handled by frontend logic
    }

    for role_value in role_permissions.keys():
        # Create the Group
        group, created = Group.objects.get_or_create(name=role_value)

        # 2. Assign Permissions for this role
        if role_value in role_permissions:
            perms_to_add = []
            for perm_str in role_permissions[role_value]:
                app_label, codename = perm_str.split(".")
                try:
                    perm = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    perms_to_add.append(perm)
                except Permission.DoesNotExist:
                    # This might happen if 'questions' app isn't migrated yet
                    print(f"Warning: Permission {perm_str} not found yet.")

            if perms_to_add:
                group.permissions.set(
                    perms_to_add
                )  # .set() replaces old perms with this new list
