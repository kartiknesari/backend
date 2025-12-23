from rest_framework import serializers
import questions.models.models_payload as payload_models
import uuid


# --- Payload serializers (nested on Question) -------------------------------
class MCQPayloadSerializer(serializers.ModelSerializer):
    options = serializers.DictField(
        child=serializers.CharField(),  # The child is the text, the key is the UUID
        help_text="Dictionary mapping id(uuid) to text(string)",
    )

    class Meta:
        model = payload_models.MCQPayload
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
        model = payload_models.NumericalPayload
        fields = ["answer", "unit", "tolerance"]


class CasePayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = payload_models.CasePayload
        fields = ["rubric"]


class DiagramPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = payload_models.DiagramPayload
        fields = ["image", "hotspots"]
