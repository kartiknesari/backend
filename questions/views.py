# questions/views.py
from typing import Type
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, permissions, filters
from .filters import QuestionFilter
from .models.models import Domain, Topic, Question  # Keep models for queryset
from .serializers import (
    DomainSerializer,
    TopicSerializer,
    QuestionSerializer,
    QuestionListSerializer,
)


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


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.filter(is_active=True)
    serializer_class = DomainSerializer
    permission_classes = [CustomDjangoModelPermissions]


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("domain").filter(domain__is_active=True)
    serializer_class = TopicSerializer
    permission_classes = [CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["domain"]
    search_fields = ["name"]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("domain", "topic", "created_by").filter(
        is_active=True
    )

    permission_classes = [CustomDjangoModelPermissions]

    # serializer_class = QuestionSerializer # Removed, now dynamically set by get_serializer_class
    def get_serializer_class(self) -> Type[QuestionSerializer | QuestionListSerializer]:  # type: ignore
        if self.action == "list":
            return QuestionListSerializer
        return QuestionSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = QuestionFilter
