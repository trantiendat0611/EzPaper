import json

from google import genai
from google.genai import types

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


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def analyze_section_with_gemini(section: PaperSection) -> tuple[str, str]:
    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=_build_prompt(section),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTIONS,
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)
    summary_vi = str(data.get("summary_vi", "")).strip()
    explanation_vi = str(data.get("explanation_vi", "")).strip()

    if not summary_vi or not explanation_vi:
        raise ValueError("Gemini response did not include the required analysis fields")

    return summary_vi, explanation_vi


def answer_question_with_gemini(context: str, question: str) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=build_qa_input(context, question),
        config=types.GenerateContentConfig(system_instruction=QA_SYSTEM_INSTRUCTIONS),
    )

    answer = response.text.strip()
    if not answer:
        raise ValueError("Gemini returned an empty answer")
    return answer


def check_gemini_connection() -> str:
    if not settings.gemini_api_key:
        return "missing_api_key"

    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents="Health check",
        config=types.GenerateContentConfig(system_instruction="Reply with exactly: ok"),
    )

    return response.text.strip()
