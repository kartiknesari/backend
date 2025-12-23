from django.db import models
import uuid
from django.forms import ValidationError


# MCQ
class MCQPayload(models.Model):
    question = models.OneToOneField(
        "questions.Question", on_delete=models.CASCADE, related_name="mcq_payload"
    )
    options = models.JSONField(  # Stores [{"id": "uuid", "text": "Option A"}, ...]
        default=dict,
        help_text='Dictionary of options, e.g., {"uuid1": "Option A", "uuid2": "Option B"}',
    )
    correct = models.JSONField(  # Stores ["uuid1", "uuid2"]
        default=dict, help_text="List of IDs of correct option(s)"
    )
    shuffle = models.BooleanField(default=True)

    def clean(self):
        if not isinstance(self.correct, list):
            raise ValidationError("`correct` must be a list of option IDs.")
        if not isinstance(self.options, dict):
            raise ValidationError("`options` must be a dictionary.")
        if len(self.options) != 4:
            raise ValidationError("There must be 4 MCQ options.")

        option_texts = set()

        # Validate keys (IDs) and values (texts) in the options dictionary
        for option_id, option_text in self.options.items():
            if not isinstance(option_id, str):
                raise ValidationError(
                    f"Option key '{option_id}' must be a string (UUID)."
                )
            if not isinstance(option_text, str):
                raise ValidationError(
                    f"Option value for ID '{option_id}' must be a string (text)."
                )
            try:
                uuid.UUID(option_id)  # Validate it's a valid UUID string
            except ValueError:
                raise ValidationError(f"Option ID '{option_id}' is not a valid UUID.")

            # Check for duplicate option texts
            if option_text in option_texts:
                raise ValidationError(
                    f"Duplicate option text found: '{option_text}'. Option texts must be unique."
                )
            option_texts.add(option_text)

        if not self.correct:
            raise ValidationError("At least one correct answer ID is mandatory.")

        # Check if all correct IDs are present in the options
        for correct_id in self.correct:
            if not isinstance(correct_id, str):
                raise ValidationError(
                    "Each correct answer must be an option ID (string)."
                )
            try:
                uuid.UUID(correct_id)  # Validate it's a valid UUID string
            except ValueError:
                raise ValidationError(
                    f"Correct answer ID '{correct_id}' is not a valid UUID."
                )

            if (
                correct_id not in self.options
            ):  # Check if ID exists as a key in options dict
                raise ValidationError(
                    f"Correct answer ID '{correct_id}' is not present in the provided options."
                )

    def save(self, *args, **kwargs):
        self.full_clean()  # Use full_clean to run model-level validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MCQ: {len(self.correct)} correct option(s)"


# Numerical
class NumericalPayload(models.Model):
    question = models.OneToOneField(
        "questions.Question", on_delete=models.CASCADE, related_name="num_payload"
    )
    answer = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    tolerance = models.FloatField(
        default=0.02, help_text="Relative tolerance (e.g., 0.02 = ±2%)"
    )

    def __str__(self):
        return f"NUM: {self.answer} {self.unit}"


# Open-Ended / Case Study
class CasePayload(models.Model):
    question = models.OneToOneField(
        "questions.Question", on_delete=models.CASCADE, related_name="case_payload"
    )
    rubric = models.JSONField(
        default=dict, help_text='{"criteria": "Safety", "max": 5, "weight": 0.4}'
    )

    def __str__(self):
        return "CASE: Rubric-based"


# Diagram
class DiagramPayload(models.Model):
    question = models.OneToOneField(
        "questions.Question", on_delete=models.CASCADE, related_name="diag_payload"
    )
    image = models.ImageField(upload_to="diagrams/")
    hotspots = models.JSONField(default=list)  # [{"x": 10, "y": 20, "label": "Pump"}]

    def __str__(self):
        return f"DIAG: {self.image.name}"
