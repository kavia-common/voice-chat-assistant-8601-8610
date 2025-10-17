from django.urls import path
from .views import health, transcribe_view, chat_view, voice_chat_view

app_name = "api"

urlpatterns = [
    path('health/', health, name='Health'),
    path('v1/transcribe/', transcribe_view, name='transcribe'),
    path('v1/chat/', chat_view, name='chat'),
    path('v1/voice-chat/', voice_chat_view, name='voice_chat'),
]
