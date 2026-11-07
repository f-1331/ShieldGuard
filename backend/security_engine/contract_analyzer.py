import io
from typing import Dict, Any, Optional
import pypdf
from backend.security_engine.llm_engine import analyze_contract_text_or_image

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """PDF baytlari ichidagi matnlarni ajratib oladi."""
    text_content = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(f"--- [Sahifa {page_idx + 1}] ---\n{page_text}")
    except Exception as e:
        return f"PDF matnini ajratishda xatolik: {str(e)}"
    
    return "\n\n".join(text_content)


async def analyze_contract_file(
    filename: str,
    file_bytes: bytes,
    mime_type: Optional[str] = None,
    raw_text: Optional[str] = None
) -> Dict[str, Any]:
    """PDF, rasm yoki to'g'ridan-to'g'ri matn ko'rinishidagi shartnomani tahlil qiladi."""
    clean_name = filename.lower()
    extracted_text = raw_text or ""
    image_bytes = None
    is_image = False

    if clean_name.endswith(".pdf") or mime_type == "application/pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
    elif any(clean_name.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]) or (mime_type and mime_type.startswith("image/")):
        is_image = True
        image_bytes = file_bytes
    elif not extracted_text:
        # Oddiy matn sifatida dekodlash
        try:
            extracted_text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            extracted_text = ""

    # LLM & Yuridik qoidalar tahlilini yuritish
    analysis_result = await analyze_contract_text_or_image(extracted_text, image_bytes)

    # Natijani standartlashtirish
    safety_score = analysis_result.get("overall_safety_score", 60)
    verdict = analysis_result.get("verdict", "suspicious")
    summary = analysis_result.get("summary_uzbek", "Shartnoma tahlili yakunlandi.")

    return {
        "filename": filename,
        "is_image": is_image,
        "text_length": len(extracted_text),
        "contract_type": analysis_result.get("contract_type", "Shartnoma"),
        "overall_safety_score": safety_score,
        "verdict": verdict,
        "summary_uz": summary,
        "dangerous_clauses": analysis_result.get("dangerous_clauses", []),
        "financial_traps": analysis_result.get("financial_traps", []),
        "recommendations": analysis_result.get("recommendations", []),
        "raw_preview": extracted_text[:1000] if extracted_text else ""
    }
