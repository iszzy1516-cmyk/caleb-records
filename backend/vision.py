"""
Document verification using vision-language models.

Supports OpenAI GPT-4o, Google Gemini, and local Ollama (LLaVA).
Configuration is read from environment variables.
"""

import os
import base64
import json
import io
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from PIL import Image

VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_VERIFY_UPLOADS = os.environ.get("VISION_VERIFY_UPLOADS", "true").lower() in ("true", "1", "yes")
VISION_MIN_CONFIDENCE = float(os.environ.get("VISION_MIN_CONFIDENCE", "0.7"))

# Document type display names used in prompts
DOCUMENT_TYPE_LABELS = {
    "clearance_cert": "Clearance Certificate",
    "jamb_result": "JAMB Result",
    "waec_result": "WAEC/NECO Result",
    "jamb_admission_letter": "JAMB Admission Letter",
    "birth_certificate": "Birth Certificate",
    "passport_photo": "Passport Photo",
    "medical": "Medical Report",
    "fee_receipt": "Fee Receipt",
    "transcript": "Transcript",
}


@dataclass
class VerificationResult:
    is_correct: bool
    confidence: float
    detected_type: str
    notes: str


def _document_label(document_type: str) -> str:
    return DOCUMENT_TYPE_LABELS.get(document_type, document_type.replace("_", " ").title())


def _image_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _load_image(file_path: str) -> Image.Image:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        try:
            import fitz  # pymupdf
        except ImportError as exc:
            raise RuntimeError("pymupdf is required for PDF verification") from exc

        doc = fitz.open(file_path)
        if len(doc) == 0:
            raise ValueError("PDF has no pages")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    return Image.open(file_path)


def _build_prompt(expected_type: str) -> str:
    label = _document_label(expected_type)
    return (
        f"You are a document verification assistant for a university records system. "
        f"A student has uploaded a file that is expected to be a '{label}'. "
        f"Examine the image carefully and determine whether the uploaded document "
        f"actually matches the expected type. "
        f"Respond ONLY with a JSON object in this exact format:\n"
        f'{{"is_correct": true|false, "confidence": 0.0-1.0, "detected_type": "short description", "notes": "brief explanation"}}\n'
        f"Use confidence >= 0.85 only when you are very sure. "
        f"Use confidence < 0.5 when the document is clearly the wrong type or unreadable."
    )


def _parse_json_response(text: str) -> VerificationResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse vision response as JSON: {text}") from exc

    return VerificationResult(
        is_correct=bool(data.get("is_correct", False)),
        confidence=float(data.get("confidence", 0.0)),
        detected_type=str(data.get("detected_type", "unknown")),
        notes=str(data.get("notes", "")),
    )


def _verify_openai(file_path: str, expected_type: str) -> VerificationResult:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    image = _load_image(file_path)
    b64 = _image_to_base64(image)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _build_prompt(expected_type)},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=300,
        temperature=0.2,
    )

    text = response.choices[0].message.content or "{}"
    return _parse_json_response(text)


def _verify_gemini(file_path: str, expected_type: str) -> VerificationResult:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    image = _load_image(file_path)
    prompt = _build_prompt(expected_type)

    response = model.generate_content([prompt, image])
    text = response.text or "{}"
    return _parse_json_response(text)


def _verify_ollama(file_path: str, expected_type: str) -> VerificationResult:
    import requests

    image = _load_image(file_path)
    b64 = _image_to_base64(image)

    payload = {
        "model": "llava",
        "prompt": _build_prompt(expected_type),
        "images": [b64],
        "stream": False,
    }

    url = f"{OLLAMA_BASE_URL}/api/generate"
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    text = data.get("response", "{}")
    return _parse_json_response(text)


def is_configured() -> bool:
    """Return True if a vision provider is available."""
    if VISION_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    if VISION_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    if VISION_PROVIDER == "ollama":
        return True
    return False


def verify_document(file_path: str, expected_type: str) -> VerificationResult:
    """Verify that the file at file_path matches the expected document type."""
    if not VISION_VERIFY_UPLOADS:
        return VerificationResult(
            is_correct=True,
            confidence=1.0,
            detected_type=_document_label(expected_type),
            notes="Verification disabled by configuration.",
        )

    if VISION_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("VISION_PROVIDER=openai but OPENAI_API_KEY is not set")
        return _verify_openai(file_path, expected_type)

    if VISION_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError("VISION_PROVIDER=gemini but GEMINI_API_KEY is not set")
        return _verify_gemini(file_path, expected_type)

    if VISION_PROVIDER == "ollama":
        return _verify_ollama(file_path, expected_type)

    raise ValueError(f"Unsupported VISION_PROVIDER: {VISION_PROVIDER}")


def should_accept(result: VerificationResult) -> bool:
    """Return True if the verification result passes the configured threshold."""
    return result.is_correct and result.confidence >= VISION_MIN_CONFIDENCE
