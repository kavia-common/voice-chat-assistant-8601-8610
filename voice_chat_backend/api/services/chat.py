from typing import Optional, List, Dict

from django.conf import settings

try:
    from openai import OpenAI  # openai>=1.x
except Exception:
    OpenAI = None  # type: ignore


def _openai_client() -> Optional["OpenAI"]:
    api_key = settings.OPENAI_API_KEY.strip() if hasattr(settings, "OPENAI_API_KEY") else ""
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


# PUBLIC_INTERFACE
def send_chat(message: str, context: str = "") -> str:
    """Send a user message to OpenAI chat completion API and return the reply.

    If OPENAI_API_KEY is not configured, returns an informative message.
    """
    client = _openai_client()
    if client is None:
        return "OpenAI is not configured. Please set OPENAI_API_KEY to enable chat replies."

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    messages: List[Dict[str, str]] = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": message})

    # openai>=1.x: client.chat.completions.create
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
    )
    # Extract the first choice content safely
    if hasattr(resp, "choices") and resp.choices:
        content = getattr(resp.choices[0].message, "content", "")
        return content or ""
    return ""
