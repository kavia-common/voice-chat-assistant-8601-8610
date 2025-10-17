#!/bin/bash
cd /home/kavia/workspace/code-generation/voice-chat-assistant-8601-8610/voice_chat_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

