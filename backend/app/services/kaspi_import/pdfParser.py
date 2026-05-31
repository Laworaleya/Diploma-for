from io import BytesIO
from typing import List, Tuple

from pypdf import PdfReader


def normalize_text(text: str) -> str:
    """Normalize PDF text without removing meaningful line breaks."""
    return (
        text.replace("\u00a0", " ")
        .replace("\u202f", " ")
        .replace("\ufeff", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, List[str]]:
    warnings: List[str] = []

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError("Не удалось прочитать PDF-файл") from exc

    pages: List[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
            warnings.append(f"Не удалось извлечь текст со страницы {index}")

        if not page_text.strip():
            warnings.append(f"На странице {index} не найден читаемый текст")
        pages.append(page_text)

    text = normalize_text("\n".join(pages))
    if not text.strip():
        warnings.append("PDF не содержит извлекаемый текст. Возможно, нужен OCR.")

    return text, warnings
