from rest_framework import serializers
import questions.models.models as models


class TopicSerializer(serializers.ModelSerializer):
    # This decorator tells Swagger the shape of the GET response
    domain = serializers.PrimaryKeyRelatedField(queryset=models.Domain.objects.all())

    class Meta:
        model = models.Topic
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


class TopicNameIdSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Topic
        fields = ["id", "name", "slug"]
