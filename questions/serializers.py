# questions/serializers.py
import uuid
from drf_spectacular.utils import (
    extend_schema_field,
    inline_serializer,
    extend_schema_serializer,
)
from rest_framework import serializers

from users.models import CustomUser
from .models import Domain, Topic, Question
from .models_payload import (
    MCQPayload,
    NumericalPayload,
    CasePayload,
    DiagramPayload,
)


class DynamicFieldsMixin:
    def __init__(self, *args, **kwargs):
        # 1. Pop the 'fields' arg so the parent Field class doesn't see it
        fields = kwargs.pop("fields", None)

        # 2. Initialize the superclass normally
        super().__init__(*args, **kwargs)

        # 3. If fields were provided, filter the current fields list
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DomainNameIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "name"]


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "slug", "name", "description", "is_active"]


class TopicSerializer(serializers.ModelSerializer):
    # This decorator tells Swagger the shape of the GET response
    domain = serializers.PrimaryKeyRelatedField(queryset=Domain.objects.all())

    class Meta:
        model = Topic
        fields = ["id", "name", "description", "domain", "slug"]
        extra_kwargs = {"slug": {"required": False}}

    def to_representation(self, instance):
        """
        This method controls the Read output.
        We swap the ID for the full {id, name} dictionary.
        """
        representation = super().to_representation(instance)

        # Replace the 'domain' ID with the serialized data
        if instance.domain:
            representation["domain"] = {
                "id": instance.domain.id,
                "name": instance.domain.name,
            }
        return representation


# --- Payload serializers (nested on Question) --------------------------------
class MCQPayloadSerializer(serializers.ModelSerializer):
    options = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dictionary mapping id(uuid) to text(string)",
    )

    class Meta:
        model = MCQPayload
        fields = ["id", "options", "correct", "shuffle"]

    def validate_options(self, options):
        if not isinstance(options, dict):
            raise serializers.ValidationError("`options` must be a dictionary.")
        if len(options) != 4:
            raise serializers.ValidationError("MCQ must have exactly 4 options.")

        option_texts = set()
        for option_id, option_text in options.items():
            if not isinstance(option_id, str):
                raise serializers.ValidationError(
                    f"Option key '{option_id}' must be a string (UUID)."
                )
            if not isinstance(option_text, str):
                raise serializers.ValidationError(
                    f"Option value for ID '{option_id}' must be a string (text)."
                )

            try:
                uuid.UUID(option_id)  # Validate it's a valid UUID string
            except ValueError:
                raise serializers.ValidationError(
                    f"Option ID '{option_id}' is not a valid UUID."
                )
            # Duplicate option IDs are implicitly handled by dictionary keys
            # Check for duplicate option texts
            if option_text in option_texts:
                raise serializers.ValidationError(
                    f"Duplicate option text found: '{option_text}'. Option texts must be unique."
                )

            option_texts.add(option_text)
        return options

    def validate_correct(self, correct):
        if not isinstance(correct, list):
            raise serializers.ValidationError("`correct` must be a list of option IDs.")
        if not correct:
            raise serializers.ValidationError(
                "At least one correct answer ID is mandatory."
            )
        # Further validation (checking against options) will happen in the main validate method
        return correct

    def validate(self, attrs):
        # The individual field validators (validate_options, validate_correct) have already run.
        # Now, check cross-field consistency.
        options = attrs.get("options")
        correct = attrs.get("correct")

        if options is not None and correct is not None:
            option_ids = set(
                options.keys()
            )  # Get all valid option IDs from the keys of the options dictionary
            for correct_id in correct:
                if not isinstance(correct_id, str):
                    raise serializers.ValidationError(
                        f"Correct answer ID '{correct_id}' must be a string."
                    )
                try:
                    uuid.UUID(correct_id)
                except ValueError:
                    raise serializers.ValidationError(
                        f"Correct answer ID '{correct_id}' is not a valid UUID."
                    )
                if correct_id not in option_ids:
                    raise serializers.ValidationError(
                        {
                            "correct": f"Correct answer ID '{correct_id}' is not present in the provided options."
                        }
                    )
        return attrs


class NumericalPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumericalPayload
        fields = ["answer", "unit", "tolerance"]


class CasePayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CasePayload
        fields = ["rubric"]


class DiagramPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagramPayload
        fields = ["image", "hotspots"]


# --- Question serializer with nested payloads -------------------------------
class QuestionSerializer(serializers.ModelSerializer):
    # Change these to PrimaryKeyRelatedField for write operations
    domain = serializers.PrimaryKeyRelatedField(queryset=Domain.objects.all())
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), allow_null=True, required=False
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), allow_null=True, required=False
    )

    # Expose payloads for read and write
    # mcq_payload = MCQPayloadSerializer(required=False, allow_null=True)
    # num_payload = NumericalPayloadSerializer(required=False, allow_null=True)
    # case_payload = CasePayloadSerializer(required=False, allow_null=True)
    # diag_payload = DiagramPayloadSerializer(required=False, allow_null=True)

    class Meta:
        model = Question
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
            # "mcq_payload",
            # "num_payload",
            # "case_payload",
            # "diag_payload",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]  # created_by is now writable, so remove from here

    def validate(self, attrs):
        # Ensure payloads provided are consistent with `type`
        qtype = attrs.get("type") or getattr(self.instance, "type", None)

        options: list = ["mcq", "num", "case", "diag"]
        if qtype not in options:
            raise serializers.ValidationError(
                detail="Payload provided does not match question `type`."
            )

        return attrs

    def to_representation(self, instance):
        """
        This method controls the Read output. We swap the ID for the full
        {id, name} dictionary for domain and topic, and string representation
        for created_by.
        """
        representation = super().to_representation(instance)

        # Replace the 'domain' ID with the serialized data
        if instance.domain:
            representation["domain"] = {
                "id": instance.domain.id,
                "name": instance.domain.name,
            }
        if instance.topic:
            representation["topic"] = {
                "id": instance.topic.id,
                "name": instance.topic.name,
            }
        return representation

    # def create(self, validated_data):
    #     # Extract payloads
    #     mcq = validated_data.pop("mcq_payload", None)
    #     num = validated_data.pop("num_payload", None)
    #     case = validated_data.pop("case_payload", None)
    #     diag = validated_data.pop("diag_payload", None)

    #     question = Question.objects.create(**validated_data)

    #     # Create payload matching type
    #     if question.type == "mcq" and mcq is not None:
    #         MCQPayload.objects.create(question=question, **mcq)
    #     elif question.type == "num" and num is not None:
    #         NumericalPayload.objects.create(question=question, **num)
    #     elif question.type == "case" and case is not None:
    #         CasePayload.objects.create(question=question, **case)
    #     elif question.type == "diag" and diag is not None:
    #         DiagramPayload.objects.create(question=question, **diag)

    #     return question

    # def update(self, instance, validated_data):
    #     # payloads
    #     mcq = validated_data.pop("mcq_payload", None)
    #     num = validated_data.pop("num_payload", None)
    #     case = validated_data.pop("case_payload", None)
    #     diag = validated_data.pop("diag_payload", None)

    #     # If type changed, remove payloads that don't match new type
    #     new_type = validated_data.get("type", instance.type)
    #     if new_type != instance.type:
    #         # delete any existing payloads
    #         for rel in ("mcq_payload", "num_payload", "case_payload", "diag_payload"):
    #             try:
    #                 obj = getattr(instance, rel)
    #                 if obj is not None:
    #                     obj.delete()
    #             except (AttributeError, instance._meta.model.DoesNotExist):
    #                 pass

    #     # Update basic fields
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()

    #     # Upsert payload for the appropriate type
    #     if instance.type == "mcq" and mcq is not None:
    #         MCQPayload.objects.update_or_create(question=instance, defaults=mcq)
    #     if instance.type == "num" and num is not None:
    #         NumericalPayload.objects.update_or_create(question=instance, defaults=num)
    #     if instance.type == "case" and case is not None:
    #         CasePayload.objects.update_or_create(question=instance, defaults=case)
    #     if instance.type == "diag" and diag is not None:
    #         DiagramPayload.objects.update_or_create(question=instance, defaults=diag)

    #     return instance

    # def to_representation(self, instance):
    #     # Default representation then remove payloads that don't match type (for clarity)
    #     ret = super().to_representation(instance)
    #     # Clear non-matching payloads
    #     mapping = {
    #         "mcq": "mcq_payload",
    #         "num": "num_payload",
    #         "case": "case_payload",
    #         "diag": "diag_payload",
    #     }
    #     expected = mapping.get(instance.type)
    #     for key in ("mcq_payload", "num_payload", "case_payload", "diag_payload"):
    #         if key != expected:
    #             ret.pop(key, None)
    #     return ret
