import json

from openai import OpenAI

from app.core.config import settings
from app.models.paper import PaperSection
from app.services.qa_prompts import QA_SYSTEM_INSTRUCTIONS, build_qa_input

SYSTEM_INSTRUCTIONS = """
You help Vietnamese beginners understand scientific papers.
Analyze only the provided section text. Do not invent details.
Return compact Vietnamese that is clear, practical, and grounded in the section.
Return valid JSON with exactly these string keys: summary_vi, explanation_vi.
"""


def _build_prompt(section: PaperSection) -> str:
    section_text = section.raw_text[:8000]
    return f"""
Paper section title: {section.title}
Section type: {section.section_type}

Section text:
{section_text}

Task:
1. summary_vi: Summarize the section in Vietnamese in 2-4 concise sentences.
2. explanation_vi: Explain the section in Vietnamese for a beginner learning programming or AI.
3. If the section is References, say it is mainly citation material and avoid over-explaining.
4. If information is missing, say that the section does not provide enough information.

Return JSON only.
"""


def analyze_section_with_openai(section: PaperSection) -> tuple[str, str]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=_build_prompt(section),
    )

    data = json.loads(response.output_text)
    summary_vi = str(data.get("summary_vi", "")).strip()
    explanation_vi = str(data.get("explanation_vi", "")).strip()

    if not summary_vi or not explanation_vi:
        raise ValueError("OpenAI response did not include the required analysis fields")

    return summary_vi, explanation_vi


def answer_question_with_openai(context: str, question: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=QA_SYSTEM_INSTRUCTIONS,
        input=build_qa_input(context, question),
    )

    answer = response.output_text.strip()
    if not answer:
        raise ValueError("OpenAI returned an empty answer")
    return answer


def check_openai_connection() -> str:
    if not settings.openai_api_key:
        return "missing_api_key"

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions="Reply with exactly: ok",
        input="Health check",
    )

    return response.output_text.strip()
