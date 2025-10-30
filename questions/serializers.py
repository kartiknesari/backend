# questions/serializers.py
from rest_framework import serializers
from .models import Domain, Topic, Question


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "slug", "name", "description", "is_active"]


class TopicSerializer(serializers.ModelSerializer):
    domain = DomainSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "slug", "name", "description", "domain"]


class QuestionSerializer(serializers.ModelSerializer):
    domain = DomainSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "domain",
            "topic",
            "type",
            "text",
            "explanation",
            "difficulty",
            "points",
            "time_estimate_seconds",
            "data",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
