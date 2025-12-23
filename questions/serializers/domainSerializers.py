from rest_framework import serializers
import questions.models.models as models


class DynamicFieldsMixin:
    fields: serializers.BindingDict

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
        model = models.Domain
        fields = ["id", "name"]


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Domain
        fields = ["id", "slug", "name", "description", "is_active"]
