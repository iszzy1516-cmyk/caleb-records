"""Re-export the root vision.py helpers used by API routes.

The actual implementation lives at repository-root/backend/vision.py so that
its environment-variable initialization stays lazy and independent of the
app package import graph.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from vision import (  # noqa: E402
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    DASHSCOPE_MODEL,
    DOCUMENT_TYPE_LABELS,
    GROQ_API_KEY,
    OVH_QWEN_API_KEY,
    OVH_QWEN_BASE_URL,
    VISION_MIN_CONFIDENCE,
    VISION_PROVIDER,
    VISION_REJECT_ON_FAILURE,
    VISION_VERIFY_UPLOADS,
    VerificationResult,
    is_configured,
    rejection_message,
    should_accept,
    verify_document,
)

__all__ = [
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_BASE_URL",
    "DASHSCOPE_MODEL",
    "DOCUMENT_TYPE_LABELS",
    "GROQ_API_KEY",
    "OVH_QWEN_API_KEY",
    "OVH_QWEN_BASE_URL",
    "VISION_MIN_CONFIDENCE",
    "VISION_PROVIDER",
    "VISION_REJECT_ON_FAILURE",
    "VISION_VERIFY_UPLOADS",
    "VerificationResult",
    "is_configured",
    "rejection_message",
    "should_accept",
    "verify_document",
]
