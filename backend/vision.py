"""
Document verification using vision-language models.

Supports OpenAI GPT-4o, Groq Llama Vision, DashScope Qwen-VL, Google Gemini,
OVH-hosted Qwen2.5-VL, and local Ollama (LLaVA).
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
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)
DASHSCOPE_MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen-vl-max")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OVH_QWEN_BASE_URL = os.environ.get(
    "OVH_QWEN_BASE_URL", "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
)
OVH_QWEN_API_KEY = os.environ.get("OVH_QWEN_API_KEY", "none")
VISION_VERIFY_UPLOADS = os.environ.get("VISION_VERIFY_UPLOADS", "true").lower() in ("true", "1", "yes")
VISION_REJECT_ON_FAILURE = os.environ.get("VISION_REJECT_ON_FAILURE", "true").lower() in ("true", "1", "yes")
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

# Detailed descriptions to help the vision model recognize each document type
DOCUMENT_TYPE_DESCRIPTIONS = {
    "jamb_result": (
        "a JAMB (Joint Admissions and Matriculation Board) result slip. "
        "It should show the JAMB logo/header, candidate's name, JAMB registration number, "
        "subject scores, total score, and year of examination. "
        "Reject unrelated images, selfies, blank pages, or documents without JAMB branding."
    ),
    "waec_result": (
        "a WAEC or NECO result slip/certificate. "
        "It should show the WAEC or NECO header/logo, candidate's name, examination number, "
        "subject names and grades, and year. "
        "Reject unrelated images, selfies, or documents without WAEC/NECO branding."
    ),
    "jamb_admission_letter": (
        "a JAMB admission letter. "
        "It should show the JAMB header/logo, candidate's name, course admitted, institution, "
        "and admission status. "
        "Reject unrelated documents or screenshots."
    ),
    "birth_certificate": (
        "a birth certificate or certificate of birth. "
        "It should show an official government/National Population Commission header, "
        "the person's full name, date of birth, place of birth, and a registration/serial number. "
        "Reject selfies, plain ID cards, or unrelated papers."
    ),
    "passport_photo": (
        "a passport photograph. "
        "It must be a clear, recent, frontal head-and-shoulders photo of one person "
        "against a plain white or light background, with no hats or dark glasses. "
        "Reject group photos, selfies, landscapes, or documents."
    ),
    "medical": (
        "a medical report or fitness certificate. "
        "It should show a hospital, clinic, or doctor's letterhead, examination details, "
        "doctor's name/signature, and official stamp. "
        "Reject unrelated documents, drug receipts, or selfies."
    ),
    "clearance_cert": (
        "a university clearance certificate. "
        "It should show the university/department header, student name, matric number, "
        "level/session cleared, and official stamp/signature. "
        "Reject unrelated papers."
    ),
    "fee_receipt": (
        "a school fee payment receipt. "
        "It should show the institution/bank header, payer name, amount paid, transaction reference, "
        "and date. Reject unrelated documents."
    ),
    "transcript": (
        "an academic transcript. "
        "It should show the institution header, student name, matric number, courses, grades, "
        "and GPA/CGPA. Reject unrelated documents."
    ),
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
    description = DOCUMENT_TYPE_DESCRIPTIONS.get(expected_type, f"a {label}")
    return (
        f"You are a strict document verification assistant for a Nigerian university records system. "
        f"A student has uploaded a file that is expected to be {description}\n\n"
        f"Carefully examine the image and decide whether it truly matches the expected type. "
        f"Be critical: if the image is a random photo, selfie, screenshot, unrelated document, "
        f"or the wrong certificate, respond is_correct=false with low confidence.\n\n"
        f"Respond ONLY with a JSON object in this exact format:\n"
        f'{{"is_correct": true|false, "confidence": 0.0-1.0, "detected_type": "short description", "notes": "brief explanation"}}\n\n'
        f"Guidelines for confidence:\n"
        f"- 0.85-1.0: the document clearly matches the expected type with correct branding/text\n"
        f"- 0.70-0.84: mostly matches but some details are unclear\n"
        f"- 0.50-0.69: resembles the type but is suspicious, blurry, or partially wrong\n"
        f"- 0.0-0.49: clearly wrong type, random image, selfie, or unreadable"
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


def _verify_openai_compatible(
    file_path: str, expected_type: str, api_key: str, base_url: str, model: str
) -> VerificationResult:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    image = _load_image(file_path)
    b64 = _image_to_base64(image)

    response = client.chat.completions.create(
        model=model,
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


def _verify_openai(file_path: str, expected_type: str) -> VerificationResult:
    return _verify_openai_compatible(
        file_path,
        expected_type,
        api_key=OPENAI_API_KEY,
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    )


def _verify_groq(file_path: str, expected_type: str) -> VerificationResult:
    return _verify_openai_compatible(
        file_path,
        expected_type,
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.2-11b-vision-preview",
    )


def _verify_dashscope(file_path: str, expected_type: str) -> VerificationResult:
    return _verify_openai_compatible(
        file_path,
        expected_type,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        model=DASHSCOPE_MODEL,
    )


def _verify_gemini(file_path: str, expected_type: str) -> VerificationResult:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

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


def _verify_qwen(file_path: str, expected_type: str) -> VerificationResult:
    import requests

    image = _load_image(file_path)
    b64 = _image_to_base64(image)

    headers = {
        "Authorization": f"Bearer {OVH_QWEN_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "Qwen2.5-VL-72B-Instruct",
        "messages": [
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
        "max_tokens": 300,
        "temperature": 0.2,
    }

    url = f"{OVH_QWEN_BASE_URL}/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"].get("content", "{}")
    return _parse_json_response(text)


def is_configured() -> bool:
    """Return True if a vision provider is available."""
    if VISION_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    if VISION_PROVIDER == "groq":
        return bool(GROQ_API_KEY)
    if VISION_PROVIDER == "dashscope":
        return bool(DASHSCOPE_API_KEY)
    if VISION_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    if VISION_PROVIDER == "qwen":
        return True
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

    if VISION_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("VISION_PROVIDER=groq but GROQ_API_KEY is not set")
        return _verify_groq(file_path, expected_type)

    if VISION_PROVIDER == "dashscope":
        if not DASHSCOPE_API_KEY:
            raise RuntimeError("VISION_PROVIDER=dashscope but DASHSCOPE_API_KEY is not set")
        return _verify_dashscope(file_path, expected_type)

    if VISION_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError("VISION_PROVIDER=gemini but GEMINI_API_KEY is not set")
        return _verify_gemini(file_path, expected_type)

    if VISION_PROVIDER == "qwen":
        return _verify_qwen(file_path, expected_type)

    if VISION_PROVIDER == "ollama":
        return _verify_ollama(file_path, expected_type)

    raise ValueError(f"Unsupported VISION_PROVIDER: {VISION_PROVIDER}")


def should_accept(result: VerificationResult) -> bool:
    """Return True if the verification result passes the configured threshold."""
    return result.is_correct and result.confidence >= VISION_MIN_CONFIDENCE


def rejection_message(expected_type: str, result: VerificationResult) -> str:
    """Return a clear, user-facing message when verification fails."""
    label = _document_label(expected_type)
    detected = result.detected_type or "unknown/unreadable document"
    confidence_pct = f"{result.confidence:.0%}"
    notes = result.notes or "The uploaded file does not appear to match the required document."
    return (
        f"Document verification failed. Expected '{label}' but detected '{detected}' "
        f"(confidence: {confidence_pct}). {notes} Please upload the correct document."
    )
