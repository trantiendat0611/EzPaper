from app.models.paper import PaperSection

SECTION_SYSTEM_INSTRUCTIONS = """
You are an expert research-paper tutor helping Vietnamese beginners (students
and newcomers to the field) deeply understand a scientific paper, one section
at a time.
Base your answer ONLY on the provided paper context and section text. Do not
invent facts, numbers, or citations that are not present in the text.
Write natural, fluent Vietnamese aimed at someone with no prior background in
the topic.
Return valid JSON with exactly these string keys: summary_vi, explanation_vi.
"""


def build_section_prompt(section: PaperSection) -> str:
    paper = section.paper
    section_text = section.raw_text[:8000]

    paper_context = f"Paper title: {paper.title}\n"
    if paper.abstract:
        paper_context += f"Paper abstract: {paper.abstract[:1500]}\n"

    return f"""
{paper_context}
This section's title: {section.title}
Section type: {section.section_type}

Section text:
{section_text}

Task:
1. summary_vi: Summarize this section in Vietnamese in 2-4 concise sentences,
   focused on its key point.
2. explanation_vi: Write a deeper, beginner-friendly explanation in Vietnamese
   (a short paragraph, or a few bullet points if that reads more clearly).
   Specifically:
   - Define any technical terms, jargon, or abbreviations that appear.
   - Explain any formulas, numbers, or results mentioned in plain language.
   - Say how this section connects to the paper's overall goal (use the
     paper title/abstract above for context).
   Do not artificially limit the length to a couple of sentences if the
   section has more to explain.
3. If the section is References, keep both fields brief and note that it is
   mainly citation material.
4. If the section text does not contain enough information, say so honestly
   in both fields instead of inventing details.

Return JSON only.
"""
