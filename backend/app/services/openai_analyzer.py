import json

from openai import OpenAI

from app.core.config import settings
from app.models.paper import PaperSection
from app.services.qa_prompts import QA_SYSTEM_INSTRUCTIONS, build_qa_input
from app.services.section_prompts import SECTION_SYSTEM_INSTRUCTIONS, build_section_prompt


def analyze_section_with_openai(section: PaperSection) -> tuple[str, str]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=SECTION_SYSTEM_INSTRUCTIONS,
        input=build_section_prompt(section),
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
