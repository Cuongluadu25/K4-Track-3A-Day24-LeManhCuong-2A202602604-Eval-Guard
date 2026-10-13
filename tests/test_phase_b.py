"""Student logic uses mock SDK; never invokes the live judge."""
from unittest.mock import Mock

import pytest

from src import phase_b_judge as phase

pytestmark = pytest.mark.student
Q,A,B,REF = "Q", "Correct detailed answer", "Wrong", "Policy reference"


def test_pairwise_uses_json_judge(openai_client):
    result = phase.pairwise_judge(Q,A,B,reference=REF)
    assert result == {"winner":"A","reasoning":"Matches the supplied policy.","scores":{"A":.9,"B":.2}}
    openai_client.chat.completions.create.assert_called_once()
    call = openai_client.chat.completions.create.call_args.kwargs
    assert REF in str(call["messages"])
    assert call["response_format"] == {"type":"json_object"}
    assert call["max_tokens"] >= 512
    import openai
    kwargs = openai.OpenAI.call_args.kwargs
    assert kwargs["default_headers"]["x-opencode-session"]


@pytest.mark.parametrize("second_raw,expected,consistent", [("B","A",True),("A","tie",False)])
def test_swap_conversion_and_calls(monkeypatch,second_raw,expected,consistent):
    mocked = Mock(side_effect=[
        {"winner":"A","reasoning":"first","scores":{"A":.9,"B":.2}},
        {"winner":second_raw,"reasoning":"second","scores":{"A":.2,"B":.9}}])
    monkeypatch.setattr(phase,"pairwise_judge",mocked)
    result = phase.swap_and_average(Q,A,B,reference=REF)
    assert mocked.call_count == 2
    assert mocked.call_args_list[0].args[:3] == (Q,A,B)
    assert mocked.call_args_list[1].args[:3] == (Q,B,A)
    assert result.winner_pass2 == ("A" if second_raw=="B" else "B")
    assert result.final_winner == expected and result.position_consistent is consistent
    assert result.scores_pass2 == {"A":.9,"B":.2}


@pytest.mark.parametrize("judge,human,expected", [
    ([1,0,1,0],[1,0,1,0],1), ([1,0,1,0],[0,1,0,1],-1),
    ([1,1,0,0],[1,0,1,0],0)])
def test_kappa_exact(judge,human,expected):
    assert phase.cohen_kappa(judge,human) == pytest.approx(expected)


def test_bias_known_counts():
    rows = [
        phase.JudgeResult(Q,A,B,"A","A","A","r1","r2",True),
        phase.JudgeResult(Q,A,B,"A","B","tie","r1","r2",False)]
    result = phase.bias_report(rows)
    assert result["total_judged"] == 2 and result["position_bias_count"] == 1
    assert result["position_bias_rate"] == .5 and result["verbosity_bias"] == 1
    assert result["interpretation"].strip()


def test_bias_empty():
    assert phase.bias_report([])["total_judged"] == 0


@pytest.mark.parametrize("judge,human", [([], []), ([1], []), ([True], [1]), ([2], [0])])
def test_kappa_rejects_invalid_labels(judge, human):
    with pytest.raises(ValueError):
        phase.cohen_kappa(judge, human)


def test_kappa_single_class_lab_convention():
    assert phase.cohen_kappa([1, 1], [1, 1]) == 0


@pytest.mark.parametrize("payload", [
    {"winner": "C", "reasoning": "reason", "scores": {"A": .9, "B": .2}},
    {"winner": "A", "reasoning": " ", "scores": {"A": .9, "B": .2}},
    {"winner": "A", "reasoning": "reason", "scores": {"A": True, "B": .2}},
    {"winner": "A", "reasoning": "reason", "scores": {"A": float("nan"), "B": .2}},
    {"winner": "A", "reasoning": "reason", "scores": {"A": 1.1, "B": .2}},
    {"winner": "A", "reasoning": "reason", "scores": {"A": .9}},
])
def test_pairwise_rejects_invalid_response(openai_client, payload):
    import json
    openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps(payload)
    with pytest.raises(ValueError):
        phase.pairwise_judge(Q, A, B, reference=REF)


def test_swap_ties_keep_reference(monkeypatch):
    mocked = Mock(return_value={"winner": "tie", "reasoning": "equal", "scores": {"A": .5, "B": .5}})
    monkeypatch.setattr(phase, "pairwise_judge", mocked)
    result = phase.swap_and_average(Q, A, B, reference=REF)
    assert result.final_winner == "tie" and result.position_consistent
    assert all(call.kwargs["reference"] == REF for call in mocked.call_args_list)


def test_bias_counts_b_winner_and_excludes_ties():
    rows = [
        phase.JudgeResult(Q, "short", "longer answer", "B", "B", "B", "r", "r", True),
        phase.JudgeResult(Q, "same", "same", "A", "A", "A", "r", "r", True),
        phase.JudgeResult(Q, A, B, "A", "B", "tie", "r", "r", False),
    ]
    result = phase.bias_report(rows)
    assert result["verbosity_bias"] == .5
    assert result["verbosity_details"] == {
        "a_wins_a_longer": 0, "b_wins_b_longer": 1, "total_decisive": 2}
