from pathlib import Path

from docx import Document

from exporters.brand_plan import to_docx, to_markdown
from tests.factories import make_brand_plan


def test_to_markdown_contains_every_required_section():
    plan = make_brand_plan()
    markdown = to_markdown(plan)

    for heading in [
        "## Situation",
        "## Key Issues",
        "## Imperatives",
        "## Positioning",
        "## Message House",
        "## Objectives",
        "## KPI Tree",
        "## Forecast",
        "## Risks & Tests",
        "## Compliance Flags",
    ]:
        assert heading in markdown


def test_to_docx_opens_and_has_expected_headings(tmp_path: Path):
    plan = make_brand_plan()
    path = to_docx(plan, tmp_path / "plan.docx")

    assert path.exists()
    doc = Document(str(path))
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert "Situation" in headings
    assert "Positioning" in headings
    assert "Forecast" in headings
    assert "Compliance Flags" in headings
