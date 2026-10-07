from uuid import uuid4

from agents.m1.gap_check import find_gaps
from agents.m1.synthesiser import QuestionCoverage, SynthesisResult

QUESTION_BANK = {
    "block_a": ["answered well", "answered poorly", "not covered at all"],
    "block_b": ["explicitly unanswered"],
}


def test_find_gaps_classifies_each_question_correctly():
    brand_id = uuid4()
    synthesis = SynthesisResult(
        question_coverage=[
            QuestionCoverage(
                block="block_a", question="answered well", answered=True, confidence=0.9
            ),
            QuestionCoverage(
                block="block_a", question="answered poorly", answered=True, confidence=0.2
            ),
            QuestionCoverage(
                block="block_b", question="explicitly unanswered", answered=False, confidence=0.0
            ),
            # "not covered at all" has no entry at all
        ]
    )

    gaps = find_gaps(brand_id, QUESTION_BANK, synthesis)
    gaps_by_question = {g.question: g for g in gaps}

    assert "answered well" not in gaps_by_question
    assert gaps_by_question["answered poorly"].reason == "low_confidence"
    assert gaps_by_question["answered poorly"].best_confidence == 0.2
    assert gaps_by_question["explicitly unanswered"].reason == "unanswered"
    assert gaps_by_question["not covered at all"].reason == "unanswered"
    assert gaps_by_question["not covered at all"].best_confidence == 0.0
    assert len(gaps) == 3
    assert all(g.brand_id == brand_id for g in gaps)
