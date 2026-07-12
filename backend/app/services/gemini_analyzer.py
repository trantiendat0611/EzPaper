import json

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.paper import PaperSection
from app.services.qa_prompts import QA_SYSTEM_INSTRUCTIONS, build_qa_input
from app.services.section_prompts import SECTION_SYSTEM_INSTRUCTIONS, build_section_prompt


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def analyze_section_with_gemini(section: PaperSection) -> tuple[str, str]:
    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=build_section_prompt(section),
        config=types.GenerateContentConfig(
            system_instruction=SECTION_SYSTEM_INSTRUCTIONS,
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
