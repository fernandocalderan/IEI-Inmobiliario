from __future__ import annotations

from typing import Any


IEI_FRAMEWORK_NAME = "IEI™"
IEI_FRAMEWORK_FULL_NAME = "IEI™ — Índice de Evaluación Integral"
IEI_FRAMEWORK_TAGLINE = "Framework propietario de evaluación determinista, versionado y auditable."
IEI_FRAMEWORK_VERSION = "1.0"
IEI_POWERED_BY = "Powered by IEI™"
IEI_LEGAL_NOTE = "IEI™ es un modelo determinista basado en reglas; no es tasación oficial."


def iei_framework_metadata() -> dict[str, Any]:
    return {
        "name": IEI_FRAMEWORK_NAME,
        "full_name": IEI_FRAMEWORK_FULL_NAME,
        "tagline": IEI_FRAMEWORK_TAGLINE,
        "version": IEI_FRAMEWORK_VERSION,
    }

