from django.conf import settings
from rest_framework import serializers


class AudioUploadSerializer(serializers.Serializer):
    """Serializer to validate uploaded audio files."""
    audio = serializers.FileField(required=True)

    def validate_audio(self, file_obj):
        # Validate MIME type if available
        content_type = getattr(file_obj, "content_type", None)
        if content_type and content_type not in settings.ALLOWED_AUDIO_MIME_TYPES:
            raise serializers.ValidationError(
                f"Unsupported audio type '{content_type}'. "
                f"Allowed: {', '.join(settings.ALLOWED_AUDIO_MIME_TYPES)}"
            )
        # Validate file size
        max_bytes = settings.MAX_AUDIO_FILE_MB * 1024 * 1024
        if file_obj.size and file_obj.size > max_bytes:
            raise serializers.ValidationError(
                f"File too large. Max {settings.MAX_AUDIO_FILE_MB} MB allowed."
            )
        return file_obj


class ChatRequestSerializer(serializers.Serializer):
    """Serializer to validate chat message requests."""
    message = serializers.CharField(required=True, allow_blank=False, max_length=4000)
    context = serializers.CharField(required=False, allow_blank=True, max_length=8000)
