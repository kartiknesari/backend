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


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.filter(is_active=True)
    serializer_class = DomainSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("domain").filter(domain__is_active=True)
    serializer_class = TopicSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["domain"]
    search_fields = ["name"]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("domain", "topic", "created_by").filter(
        is_active=True
    )
    # serializer_class = QuestionSerializer # Removed, now dynamically set by get_serializer_class

    def get_serializer_class(self) -> Type[QuestionSerializer | QuestionListSerializer]:  # type: ignore
        if self.action == "list":
            return QuestionListSerializer
        return QuestionSerializer

    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend]
    filterset_class = QuestionFilter

    # Disabled because filterset_class takes precedence between the both
    # Choose either but filterset_class is more powerful and explicit
    # filterset_fields = ["domain__slug", "topic__slug", "type"]

    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     domain = self.request.query_params.get("domain")
    #     topic = self.request.query_params.get("topic")
    #     qtype = self.request.query_params.get("type")
    #     if domain:
    #         qs = qs.filter(domain__slug=domain)
    #     if topic:
    #         qs = qs.filter(topic__slug=topic)
    #     if qtype:
    #         qs = qs.filter(type=qtype)
    #     return qs
