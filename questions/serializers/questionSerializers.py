from users.models import CustomUser
import questions.models.models as models
import questions.models.models_payload as payload_models
from rest_framework import serializers  # noqa
from . import DomainNameIdSerializer, TopicNameIdSlugSerializer  # noqa
from . import (
    MCQPayloadSerializer,
    NumericalPayloadSerializer,
    CasePayloadSerializer,
    DiagramPayloadSerializer,
)  # noqa


# --- Question serializer with nested payloads -------------------------------
class QuestionSerializer(serializers.ModelSerializer):
    # Foriegn Keys
    domain = serializers.PrimaryKeyRelatedField(queryset=models.Domain.objects.all())
    topic = serializers.PrimaryKeyRelatedField(
        queryset=models.Topic.objects.all(), allow_null=True, required=False
    )
    created_by = serializers.PrimaryKeyRelatedField(  # type: ignore
        queryset=CustomUser.objects.all(), allow_null=True, required=False
    )

    # Expose payloads for read and write
    mcq_payload = MCQPayloadSerializer(required=False, allow_null=True)
    num_payload = NumericalPayloadSerializer(required=False, allow_null=True)
    case_payload = CasePayloadSerializer(required=False, allow_null=True)
    diag_payload = DiagramPayloadSerializer(required=False, allow_null=True)

    class Meta:
        model = models.Question
        fields = [
            "id",
            "domain",
            "topic",
            "type",
            "question",
            "description",
            "difficulty",
            "points",
            "time_estimate_seconds",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "mcq_payload",
            "num_payload",
            "case_payload",
            "diag_payload",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]  # created_by is now writable, so remove from here

    # ... (validate, to_representation, _get_payload_model_and_data, create, update methods) ...
    def validate(self, attrs):
        # Ensure payloads provided are consistent with `type`
        qtype = attrs.get("type") or getattr(self.instance, "type", None)

        # List of all possible payload types
        payload_types = ["mcq", "num", "case", "diag"]

        # Check if the provided type is valid
        if qtype not in payload_types:
            raise serializers.ValidationError(
                {"type": "Invalid question type provided."}
            )

        # Check that only one payload is provided and it matches the question type
        provided_payloads = [
            p_type
            for p_type in payload_types
            if attrs.get(f"{p_type}_payload") is not None
        ]

        if len(provided_payloads) > 1:
            raise serializers.ValidationError(
                {"payloads": "Only one payload type can be provided per question."}
            )
        if len(provided_payloads) == 1 and provided_payloads[0] != qtype:
            raise serializers.ValidationError(
                {
                    "payloads": f"Provided payload type '{provided_payloads[0]}' does not match question type '{qtype}'."
                }
            )
        if (
            len(provided_payloads) == 0 and self.instance is None
        ):  # For create operations, a payload is required
            raise serializers.ValidationError(
                {
                    "payloads": f"A payload for type '{qtype}' is required for new questions."
                }
            )

        return attrs

    def to_representation(self, instance):
        """
        This method controls the Read output.
        - Swaps IDs for full {id, name} dictionary for domain and topic.
        - Provides string representation for created_by.
        - Clears non-matching payloads based on the question's 'type'.
        """
        representation = super().to_representation(instance)

        # Replace the 'domain' ID with the serialized data
        if instance.domain:
            representation["domain"] = DomainNameIdSerializer(instance.domain).data
        else:
            representation["domain"] = None

        # Replace the 'topic' ID with the serialized data
        if instance.topic:
            representation["topic"] = TopicNameIdSlugSerializer(instance.topic).data
        else:
            representation["topic"] = None

        # Replace the 'created_by' ID with its string representation
        if instance.created_by:
            representation["created_by"] = str(instance.created_by)
        else:
            representation["created_by"] = None

        # Clear non-matching payloads (logic from the commented-out section)
        mapping = {
            "mcq": "mcq_payload",
            "num": "num_payload",
            "case": "case_payload",
            "diag": "diag_payload",
        }
        expected_payload_key = mapping.get(instance.type)
        for key in mapping.values():
            if key != expected_payload_key:
                representation.pop(key, None)
        return representation

    def _get_payload_model_and_data(self, validated_data):
        """Helper to extract payload data and map to model classes."""
        payload_map = {
            "mcq": (payload_models.MCQPayload, validated_data.pop("mcq_payload", None)),
            "num": (
                payload_models.NumericalPayload,
                validated_data.pop("num_payload", None),
            ),
            "case": (
                payload_models.CasePayload,
                validated_data.pop("case_payload", None),
            ),
            "diag": (
                payload_models.DiagramPayload,
                validated_data.pop("diag_payload", None),
            ),
        }
        return payload_map

    def create(self, validated_data):
        # Extract payload data before creating the Question instance
        payload_map = self._get_payload_model_and_data(validated_data)

        question = models.Question.objects.create(**validated_data)

        # Create payload matching type
        payload_model_class, payload_data = payload_map.get(question.type, (None, None))
        if payload_model_class and payload_data is not None:
            payload_model_class.objects.create(question=question, **payload_data)

        return question

    def update(self, instance, validated_data):
        # Extract payload data
        payload_map = self._get_payload_model_and_data(validated_data)

        # If type changed, remove payloads that don't match new type
        new_type = validated_data.get("type", instance.type)
        if new_type != instance.type:
            # Delete any existing payloads associated with the old type
            # Iterate through all possible payload types and delete if they exist
            for q_type, (payload_model_class, _) in payload_map.items():
                try:
                    # Access the related object via its related_name
                    # For OneToOneField, if the related object doesn't exist, it raises DoesNotExist
                    related_payload_obj = getattr(instance, f"{q_type}_payload")
                    related_payload_obj.delete()
                except payload_model_class.DoesNotExist:
                    # No payload of this type existed for the old question type, which is fine.
                    pass
                except AttributeError:
                    # This should not happen if related_name is correctly defined on the models.
                    pass

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Upsert the new payload if provided and matches the question's type
        payload_model_class, payload_data = payload_map.get(new_type, (None, None))
        if payload_model_class and payload_data is not None:
            payload_model_class.objects.update_or_create(
                question=instance, defaults=payload_data
            )

        return instance


# list view without payloads
class QuestionListSerializer(serializers.ModelSerializer):
    # Foreign Keys - read-only for list view, showing name/slug for better context
    domain = DomainNameIdSerializer(read_only=True)
    topic = TopicNameIdSlugSerializer(read_only=True)
    created_by = serializers.StringRelatedField(
        read_only=True
    )  # Assumes CustomUser has a __str__ method

    class Meta:
        model = models.Question
        fields = [
            "id",
            "domain",
            "topic",
            "type",
            "question",
            "description",
            "difficulty",
            "points",
            "time_estimate_seconds",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            # Payloads are EXCLUDED here
        ]
        read_only_fields = fields  # All fields are read-only for list view

    def to_representation(self, instance):
        # Use the base to_representation as no payload clearing is needed
        return super().to_representation(instance)
