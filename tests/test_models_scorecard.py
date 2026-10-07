from models.scorecard import build_kpi_result, build_kpi_results
from schemas.brand_plan import KpiNode, KpiTree


def test_build_kpi_result_green_within_10_percent():
    result = build_kpi_result("reach", "activity", actual=95.0, plan=100.0)
    assert result.rag == "green"
    assert result.variance == -5.0


def test_build_kpi_result_amber_within_25_percent():
    result = build_kpi_result("reach", "activity", actual=80.0, plan=100.0)
    assert result.rag == "amber"


def test_build_kpi_result_red_beyond_25_percent():
    result = build_kpi_result("reach", "activity", actual=50.0, plan=100.0)
    assert result.rag == "red"


def test_build_kpi_result_no_rag_without_a_plan():
    result = build_kpi_result("reach", "activity", actual=50.0, plan=None)
    assert result.rag is None
    assert result.variance is None


def test_build_kpi_result_zero_plan_edge_case():
    assert build_kpi_result("x", "activity", actual=0.0, plan=0.0).rag == "green"
    assert build_kpi_result("x", "activity", actual=5.0, plan=0.0).rag == "red"


def test_build_kpi_results_categorizes_leading_vs_lagging():
    kpi_tree = KpiTree(
        leading=[KpiNode(name="reach", target=100.0), KpiNode(name="engagement_index", target=50.0)],
        lagging=[KpiNode(name="nrx", target=20.0)],
    )
    actuals = {"reach": 90.0, "engagement_index": 40.0, "nrx": 25.0}
    results = build_kpi_results(kpi_tree, actuals)
    by_name = {r.name: r for r in results}
    assert by_name["reach"].category == "activity"
    assert by_name["engagement_index"].category == "engagement"
    assert by_name["nrx"].category == "outcome"


def test_build_kpi_results_skips_nodes_without_an_actual():
    kpi_tree = KpiTree(leading=[KpiNode(name="reach", target=100.0)], lagging=[])
    results = build_kpi_results(kpi_tree, actuals={})
    assert results == []
