from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.paper import Paper, PaperSection
from app.services.section_analyzer import analyze_paper_sections


def test_gemini_provider_populates_section_analysis(monkeypatch, client) -> None:
    old_ai_provider = settings.ai_provider
    old_gemini_api_key = settings.gemini_api_key
    settings.ai_provider = "gemini"
    settings.gemini_api_key = "test-key"

    def fake_gemini_analysis(section: PaperSection) -> tuple[str, str]:
        return (
            f"AI summary for {section.title}",
            f"AI explanation for {section.title}",
        )

    monkeypatch.setattr(
        "app.services.section_analyzer.analyze_section_with_gemini",
        fake_gemini_analysis,
    )

    db_override = next(iter(client.app.dependency_overrides.values()))
    db_generator = db_override()
    db: Session = next(db_generator)
    try:
        paper = Paper(
            user_id=1,
            title="Gemini Test",
            original_filename="gemini-test.pdf",
            stored_filename="gemini-test.pdf",
            status="completed",
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        section = PaperSection(
            paper_id=paper.id,
            title="Abstract",
            section_type="abstract",
            order_index=0,
            raw_text="This paper introduces a useful system.",
        )
        db.add(section)
        db.commit()
        db.refresh(paper)

        analyzed, provider = analyze_paper_sections(db, paper)

        assert provider == "gemini"
        assert analyzed.status == "analyzed"
        assert analyzed.sections[0].summary_vi == "AI summary for Abstract"
        assert analyzed.sections[0].explanation_vi == "AI explanation for Abstract"
    finally:
        settings.ai_provider = old_ai_provider
        settings.gemini_api_key = old_gemini_api_key
        db.close()
        db_generator.close()
