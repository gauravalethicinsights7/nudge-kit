from exporters.scorecard import to_csv, to_markdown
from tests.factories import make_scorecard


def test_to_csv_has_header_and_one_row_per_kpi():
    scorecard = make_scorecard()
    csv_text = to_csv(scorecard)
    lines = csv_text.splitlines()
    assert lines[0] == "name,category,actual,plan,variance,rag"
    assert len(lines) == len(scorecard.kpis) + 1


def test_to_markdown_contains_period_and_kpi_table():
    scorecard = make_scorecard()
    md = to_markdown(scorecard)
    assert scorecard.period in md
    assert "engagement_index" in md
    assert "| KPI | Actual | Plan | Variance | RAG |" in md


def test_to_markdown_omits_categories_with_no_kpis():
    scorecard = make_scorecard()  # factory only has an "engagement" kpi
    md = to_markdown(scorecard)
    assert "## Activity" not in md
    assert "## Outcome" not in md
    assert "## Engagement" in md
