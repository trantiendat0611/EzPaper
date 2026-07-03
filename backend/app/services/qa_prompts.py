QA_SYSTEM_INSTRUCTIONS = """
You answer questions about a scientific paper for Vietnamese readers.
Answer ONLY based on the provided paper content. Do not invent facts.
If the paper does not contain enough information to answer, say so honestly in Vietnamese.
Reply in clear, concise Vietnamese.
"""


def build_qa_input(context: str, question: str) -> str:
    return f"Paper content:\n{context}\n\nQuestion: {question}\n\nAnswer in Vietnamese:"
