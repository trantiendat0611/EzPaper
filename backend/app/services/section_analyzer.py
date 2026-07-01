import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.paper import Paper, PaperSection
from app.services.gemini_analyzer import analyze_section_with_gemini
from app.services.openai_analyzer import analyze_section_with_openai

SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")

SECTION_GUIDES = {
    "abstract": "Phan nay tom tat muc tieu, bai toan, cach tiep can va ket qua chinh cua bai bao.",
    "introduction": "Phan nay giai thich boi canh, van de can giai quyet va ly do nghien cuu nay quan trong.",
    "background": "Phan nay cung cap kien thuc nen de nguoi doc hieu cac khai niem duoc dung trong bai.",
    "related_work": "Phan nay so sanh nghien cuu hien tai voi cac cong trinh da co truoc do.",
    "method": "Phan nay mo ta phuong phap, thuat toan, mo hinh hoac quy trinh ma tac gia de xuat.",
    "experiments": "Phan nay mo ta cach tac gia thiet ke thi nghiem, du lieu, metric va cac cau hinh danh gia.",
    "results": "Phan nay trinh bay ket qua chinh va cho biet phuong phap co hieu qua ra sao.",
    "discussion": "Phan nay dien giai y nghia cua ket qua, diem manh, gioi han va cac quan sat quan trong.",
    "conclusion": "Phan nay tom lai dong gop chinh va thuong goi mo huong phat trien tiep theo.",
    "references": "Phan nay la danh sach tai lieu tham khao, thuong khong can phan tich sau trong MVP.",
    "full_text": "Noi dung chua tach duoc thanh section ro rang, nen day la phan tong hop tam thoi tu toan van.",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def get_lead_sentences(text: str, max_sentences: int = 3, max_chars: int = 700) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return ""

    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(normalized) if sentence.strip()]
    if not sentences:
        return normalized[:max_chars]

    selected = " ".join(sentences[:max_sentences])
    return selected[:max_chars].strip()


def build_summary_vi(section: PaperSection) -> str:
    lead_text = get_lead_sentences(section.raw_text, max_sentences=3, max_chars=700)
    if not lead_text:
        return "Chua co du lieu du de tom tat section nay."

    return (
        "Tom tat so bo: section nay tap trung vao cac y chinh sau trong noi dung goc: "
        f"{lead_text}"
    )


def build_explanation_vi(section: PaperSection) -> str:
    guide = SECTION_GUIDES.get(section.section_type, SECTION_GUIDES["full_text"])
    lead_text = get_lead_sentences(section.raw_text, max_sentences=2, max_chars=500)

    return (
        f"Giai thich de hieu: {guide} "
        "Khi doc section nay, hay tim xem tac gia dang tra loi cau hoi nao, "
        "bang chung nao duoc dua ra, va y nay lien quan the nao den muc tieu chinh cua bai bao. "
        f"Doan noi dung nen bat dau chu y la: {lead_text}"
    ).strip()


def analyze_section(section: PaperSection) -> str:
    provider = settings.ai_provider

    use_gemini = provider == "gemini" or (provider == "auto" and bool(settings.gemini_api_key))
    if use_gemini:
        try:
            summary_vi, explanation_vi = analyze_section_with_gemini(section)
            section.summary_vi = summary_vi
            section.explanation_vi = explanation_vi
            return "gemini"
        except Exception:
            if provider == "gemini":
                raise

    use_openai = provider == "openai" or (provider == "auto" and bool(settings.openai_api_key))
    if use_openai:
        try:
            summary_vi, explanation_vi = analyze_section_with_openai(section)
            section.summary_vi = summary_vi
            section.explanation_vi = explanation_vi
            return "openai"
        except Exception:
            if provider == "openai":
                raise

    section.summary_vi = build_summary_vi(section)
    section.explanation_vi = build_explanation_vi(section)
    return "local"


def analyze_paper_sections(db: Session, paper: Paper) -> tuple[Paper, str]:
    paper.status = "analyzing"
    db.commit()
    db.refresh(paper)

    providers_used: set[str] = set()
    for section in paper.sections:
        providers_used.add(analyze_section(section))

    paper.status = "analyzed"
    db.commit()
    db.refresh(paper)

    provider = "openai" if "openai" in providers_used else "local"
    return paper, provider
