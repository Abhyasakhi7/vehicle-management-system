from rest_framework import serializers

from apps.vehicles.models import Vehicle

from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = (
            "id",
            "vehicle",
            "title",
            "description",
            "due_date",
            "due_mileage",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["vehicle"].queryset = Vehicle.objects.filter(owner=request.user)
        else:
            self.fields["vehicle"].queryset = Vehicle.objects.none()

    def validate(self, attrs):
        instance = self.instance
        due_date = attrs.get("due_date", instance.due_date if instance else None)
        due_mileage = attrs.get(
            "due_mileage", instance.due_mileage if instance else None
        )
        if due_date is None and due_mileage is None:
            raise serializers.ValidationError(
                "Set at least one of due date or due mileage for a reminder."
            )
        return attrs
