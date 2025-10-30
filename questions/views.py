# questions/views.py
from rest_framework import viewsets, permissions
from .models import Domain, Topic, Question
from .serializers import DomainSerializer, TopicSerializer, QuestionSerializer


class DomainViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Domain.objects.filter(is_active=True)
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.select_related("domain").filter(domain__is_active=True)
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("domain", "topic", "created_by").filter(
        is_active=True
    )
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        domain = self.request.query_params.get("domain")
        topic = self.request.query_params.get("topic")
        qtype = self.request.query_params.get("type")
        if domain:
            qs = qs.filter(domain__slug=domain)
        if topic:
            qs = qs.filter(topic__slug=topic)
        if qtype:
            qs = qs.filter(type=qtype)
        return qs
