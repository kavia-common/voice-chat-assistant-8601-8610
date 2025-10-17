from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import AudioUploadSerializer, ChatRequestSerializer
from .services.transcribe import transcribe_audio
from .services.chat import send_chat
from .utils.audio import save_uploaded_file_temporarily, safe_unlink


@api_view(['GET'])
def health(request):
    """Simple health endpoint."""
    return Response({"message": "Server is up!"})


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id='transcribe_audio',
    operation_summary='Transcribe Audio',
    operation_description='Upload an audio file (wav or mp3) to receive a transcription. Uses OpenAI if configured, else falls back to SpeechRecognition.',
    manual_parameters=[],
    request_body=None,
    responses={
        200: openapi.Response(
            description="Transcription successful",
            examples={
                "application/json": {"ok": True, "transcript": "Hello world"}
            },
        ),
        400: "Validation error",
        500: "Server error",
    },
    tags=['transcription'],
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def transcribe_view(request):
    """Transcribe an uploaded audio file.

    Body (multipart/form-data):
      - audio: file (wav/mp3)

    Returns:
      JSON { ok: bool, transcript?: str, error?: str }
    """
    serializer = AudioUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    file_obj = serializer.validated_data['audio']
    tmp_path = None
    try:
        tmp_path, _ = save_uploaded_file_temporarily(file_obj)
        ok, result = transcribe_audio(tmp_path)
        if ok:
            if getattr(settings, "DEBUG_TRANSCRIPTS", False):
                return Response({"ok": True, "transcript": result, "debug": True})
            return Response({"ok": True, "transcript": result})
        return Response({"ok": False, "error": result}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        safe_unlink(tmp_path)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id='chat',
    operation_summary='Chat',
    operation_description='Send a user message and optionally a context to get a reply from OpenAI Chat Completions.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['message'],
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='User message'),
            'context': openapi.Schema(type=openapi.TYPE_STRING, description='Optional system context/instructions'),
        },
    ),
    responses={
        200: openapi.Response(
            description="Chat response",
            examples={"application/json": {"ok": True, "reply": "Hi! How can I help you today?"}},
        ),
        400: "Validation error",
        500: "Server error",
    },
    tags=['chat'],
)
@api_view(['POST'])
@parser_classes([JSONParser])
def chat_view(request):
    """Return a chat reply from OpenAI based on the message and optional context."""
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    message = serializer.validated_data['message']
    context = serializer.validated_data.get('context', "")

    try:
        reply = send_chat(message=message, context=context)
        return Response({"ok": True, "reply": reply})
    except Exception as ex:
        return Response({"ok": False, "error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id='voice_chat',
    operation_summary='Voice Chat',
    operation_description='Upload an audio file to get transcript and a chat reply in one call.',
    manual_parameters=[],
    request_body=None,
    responses={
        200: openapi.Response(
            description="Voice chat response",
            examples={
                "application/json": {
                    "ok": True,
                    "transcript": "What is the weather today?",
                    "reply": "The weather looks sunny with a high of 75°F.",
                }
            },
        ),
        400: "Validation error",
        500: "Server error",
    },
    tags=['voice-chat'],
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def voice_chat_view(request):
    """Transcribe uploaded audio and immediately get a chat completion."""
    serializer = AudioUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    file_obj = serializer.validated_data['audio']
    tmp_path = None
    try:
        tmp_path, _ = save_uploaded_file_temporarily(file_obj)
        ok, result = transcribe_audio(tmp_path)
        if not ok:
            return Response({"ok": False, "error": result}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        transcript = result.strip()
        if not transcript:
            return Response({"ok": False, "error": "Transcript is empty."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        reply = send_chat(message=transcript, context="")
        return Response({"ok": True, "transcript": transcript, "reply": reply})
    finally:
        safe_unlink(tmp_path)
