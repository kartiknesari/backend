# In a new file, e.g., questions/filters.py
import django_filters
from .models import Question


class QuestionFilter(django_filters.FilterSet):
    domain = django_filters.CharFilter(field_name="domain__slug")
    topic = django_filters.CharFilter(field_name="topic__slug")
    # The 'type' filter is already handled by its field name

    class Meta:
        model = Question
        fields = ["domain", "topic", "type"]
