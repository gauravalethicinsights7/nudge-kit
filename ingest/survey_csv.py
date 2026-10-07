"""CSV -> SurveyResponse[] ingest for M3's survey derivation path
(agents/m3/survey.py). Wide format: respondent_id + one column per rated
item (driver/barrier Likert scores) — whatever columns exist besides
respondent_id become that response's `items` dict.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from agents.m3.survey import SurveyResponse
from ingest.csv_utils import read_csv_skipping_comments


def load_survey_csv(path: Path | str) -> list[SurveyResponse]:
    df = read_csv_skipping_comments(Path(path))
    item_columns = [c for c in df.columns if c != "respondent_id"]
    return [
        SurveyResponse(
            respondent_id=str(row["respondent_id"]),
            items={col: float(row[col]) for col in item_columns if not pd.isna(row[col])},
        )
        for _, row in df.iterrows()
    ]
