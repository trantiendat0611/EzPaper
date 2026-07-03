import re

from app.core.config import settings
from app.models.paper import Paper
from app.services.gemini_analyzer import answer_question_with_gemini
from app.services.openai_analyzer import answer_question_with_openai
from app.services.section_analyzer import get_lead_sentences

CONTEXT_CHAR_BUDGET = 12000


def build_paper_context(paper: Paper) -> str:
    parts: list[str] = []
    used = 0
    for section in paper.sections:
        if used >= CONTEXT_CHAR_BUDGET:
            break
        header = f"## {section.title}\n"
        body = section.raw_text[: CONTEXT_CHAR_BUDGET - used]
        parts.append(header + body)
        used += len(header) + len(body)
    return "\n\n".join(parts)


def _local_answer(paper: Paper, question: str) -> str:
    keywords = {word.lower() for word in re.findall(r"\w+", question) if len(word) > 3}

    best_section = None
    best_score = 0
    for section in paper.sections:
        text = section.raw_text.lower()
        score = sum(text.count(keyword) for keyword in keywords)
        if score > best_score:
            best_score = score
            best_section = section

    if best_section is None or best_score == 0:
        return (
            "Chua cau hinh AI provider nen chua the tra loi chi tiet. "
            "Hay dat GEMINI_API_KEY hoac OPENAI_API_KEY de dung day du tinh nang hoi-dap."
        )

    lead = get_lead_sentences(best_section.raw_text, max_sentences=3, max_chars=600)
    return f'Dua tren phan "{best_section.title}": {lead}'


def answer_question(paper: Paper, question: str) -> tuple[str, str]:
    context = build_paper_context(paper)
    provider = settings.ai_provider

    use_gemini = provider == "gemini" or (provider == "auto" and bool(settings.gemini_api_key))
    if use_gemini:
        try:
            return answer_question_with_gemini(context, question), "gemini"
        except Exception:
            if provider == "gemini":
                raise

    use_openai = provider == "openai" or (provider == "auto" and bool(settings.openai_api_key))
    if use_openai:
        try:
            return answer_question_with_openai(context, question), "openai"
        except Exception:
            if provider == "openai":
                raise

    return _local_answer(paper, question), "local"
