from django.contrib import admin
from .models import Domain, Topic, Question


# Register your models here.
@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "slug")
    list_filter = ("domain",)
    search_fields = ("name",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "text_preview",
        "domain",
        "topic",
        "type",
        "difficulty",
        "points",
        "is_active",
    )
    list_filter = ("domain", "type", "difficulty", "is_active")
    search_fields = ("text", "explanation")
    readonly_fields = ("id", "created_at", "updated_at")

    def text_preview(self, obj):
        preview = obj.text[:80] + ("..." if len(obj.text) > 80 else "")
        preview.short_description = "Question"
        return preview

    def question_type(self, obj):
        display = obj.get_type_display()  # ← Correct: call the method
        display.short_description = "Type"
        return display
