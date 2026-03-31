from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, List

# Common OCR misreads -> corrected tokens.
# NOTE: Keys are regex patterns; values are replacement strings.
OCR_CORRECTIONS: dict[str, str] = {
    r"\b0ef\b": "def",  # 0 confused with d
    r"\bprlnt\b": "print",  # l confused with i
    r"\bretum\b": "return",  # rn confused with m
    r"\bimpart\b": "import",  # a confused with o
    r"\bTme\b": "True",
    r"\bFa1se\b": "False",
}


class CodeLanguage(Enum):
    PYTHON = auto()
    FASTAPI = auto()
    REACT = auto()
    UNKNOWN = auto()


@dataclass
class ReconstructedCode:
    language: CodeLanguage
    raw_text: str
    cleaned_code: str
    file_extension: str
    confidence: float


class CodeReconstructor:
    """Reconstructs code from OCR text lines."""

    def reconstruct(self, ocr_lines: Iterable[str]) -> ReconstructedCode:
        raw_text = "\n".join(ocr_lines)
        corrected = self.apply_ocr_corrections(raw_text)
        lines = corrected.split("\n")

        language = self.detect_language(lines)
        if language in (CodeLanguage.PYTHON, CodeLanguage.FASTAPI):
            lines = self.infer_indentation(lines)

        cleaned = "\n".join(lines)
        ext_map = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.FASTAPI: ".py",
            CodeLanguage.REACT: ".tsx",
            CodeLanguage.UNKNOWN: ".txt",
        }

        return ReconstructedCode(
            language=language,
            raw_text=raw_text,
            cleaned_code=cleaned,
            file_extension=ext_map[language],
            confidence=self._score_confidence(cleaned, language),
        )

    def apply_ocr_corrections(self, text: str) -> str:
        """Apply regex-based OCR corrections to a text block."""
        corrected = text
        for pattern, replacement in OCR_CORRECTIONS.items():
            corrected = re.sub(pattern, replacement, corrected)
        return corrected

    def detect_language(self, lines: List[str]) -> CodeLanguage:
        """Heuristic language detection based on common tokens."""
        text = "\n".join(lines)

        # FastAPI detection
        if re.search(r"\bfrom\s+fastapi\s+import\b", text) or "FastAPI(" in text:
            return CodeLanguage.FASTAPI

        # React / TSX detection
        if (
            re.search(r"\bimport\s+React\b", text)
            or re.search(r"\bfrom\s+['\"]react['\"]", text)
            or re.search(r"\buseState\(", text)
            or re.search(r"\buseEffect\(", text)
        ):
            return CodeLanguage.REACT

        # Python detection
        if re.search(r"\bdef\s+\w+\s*\(", text) or re.search(
            r"\bclass\s+\w+\s*[:(]", text
        ):
            return CodeLanguage.PYTHON

        return CodeLanguage.UNKNOWN

    def infer_indentation(self, lines: List[str]) -> List[str]:
        """Normalize indentation for Python-like code."""
        normalized = []
        for line in lines:
            # Convert tabs to 4 spaces and strip trailing spaces
            normalized.append(line.replace("\t", "    ").rstrip())
        return normalized

    def _score_confidence(self, cleaned: str, language: CodeLanguage) -> float:
        """Simple heuristic confidence score in [0, 1]."""
        if not cleaned.strip():
            return 0.0

        score = 0.4
        if language != CodeLanguage.UNKNOWN:
            score += 0.2

        # Boost for common code tokens
        token_hits = len(
            re.findall(r"\b(def|class|import|return|const|let)\b", cleaned)
        )
        if token_hits >= 1:
            score += 0.2
        if token_hits >= 3:
            score += 0.2

        return max(0.0, min(1.0, score))
