from .domainSerializers import (
    DomainSerializer,
    DomainNameIdSerializer,
)
from .topicSerializers import (
    TopicSerializer,
    TopicNameIdSlugSerializer,
)
from .payloadSerializers import (
    MCQPayloadSerializer,
    NumericalPayloadSerializer,
    CasePayloadSerializer,
    DiagramPayloadSerializer,
)
from .questionSerializers import QuestionSerializer, QuestionListSerializer

# Define __all__ for explicit exports if desired, which helps with tools like 'from .serializers import *'
__all__ = [
    "DomainSerializer",
    "DomainNameIdSerializer",
    "TopicSerializer",
    "TopicNameIdSlugSerializer",
    "MCQPayloadSerializer",
    "NumericalPayloadSerializer",
    "CasePayloadSerializer",
    "DiagramPayloadSerializer",
    "QuestionSerializer",
    "QuestionListSerializer",
]
