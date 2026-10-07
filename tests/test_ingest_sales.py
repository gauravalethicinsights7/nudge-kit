from ingest.sales_csv import load_sales_csv

FIXTURE_PATH = "fixtures/sales_sample.csv"


def test_load_sales_csv_round_trips():
    sales = load_sales_csv(FIXTURE_PATH)
    assert len(sales) == 4
    assert sales[("63213b75-049d-4233-a85a-5f38d282821c", "2026-01")] == (2.0, 8.0)
    assert sales[("63213b75-049d-4233-a85a-5f38d282821c", "2026-02")] == (3.0, 10.0)


def test_load_sales_csv_missing_key_raises_keyerror():
    sales = load_sales_csv(FIXTURE_PATH)
    assert ("nonexistent", "2026-01") not in sales
