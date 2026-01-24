"""
Verification subsystem for sdqctl.

Provides tools for checking code references, links, terminology,
traceability, and assertions.
"""

from .base import VerificationError, VerificationResult, Verifier
from .refs import RefsVerifier
from .links import LinksVerifier
from .traceability import TraceabilityVerifier
from .terminology import TerminologyVerifier

# Registry of available verifiers
VERIFIERS: dict[str, type] = {
    "refs": RefsVerifier,
    "links": LinksVerifier,
    "traceability": TraceabilityVerifier,
    "terminology": TerminologyVerifier,
}

__all__ = [
    "VerificationError",
    "VerificationResult", 
    "Verifier",
    "RefsVerifier",
    "LinksVerifier",
    "TraceabilityVerifier",
    "TerminologyVerifier",
    "VERIFIERS",
]
