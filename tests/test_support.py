"""Regression tests for supplied support code; these pass while student TODOs remain."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from config import ADVERSARIAL_SET_PATH,CLEAN_SET_PATH,OUTPUT_SET_PATH,TEST_SET_PATH,HUMAN_LABELS_PATH
from src.experiment_support import judge_binary,metadata,percentiles,read_json,summarize_latency,write_json
from src.report_contracts import validate_phase_c,validate_latency,validate_markdown
from src.phase_a_ragas import RagasResult,build_phase_a_report

pytestmark = pytest.mark.support


def test_export_uses_student_diagnosis():
    result=RagasResult(1,"factual","Q","A",["C"],"GT",.9,.8,.7,.6)
    bottom=[{"rank":1,"question_id":1,"diagnosis":"student-specific diagnosis",
             "suggested_fix":"student-specific fix"}]
    report=build_phase_a_report([result],{"matrix":{}},bottom)
    assert report["bottom_10"]==bottom
    assert report["per_question"][0]["answer"]=="A"


def test_binary_prompt_excludes_human_labels_and_notes():
    client=Mock()
    client.chat.completions.create.return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"label":1,"reasoning":"correct"}'))])
    assert judge_binary("Q","supplied model answer","reference",client=client)["label"]==1
    packet=json.loads(client.chat.completions.create.call_args.kwargs["messages"][1]["content"])
    assert packet=={"question":"Q","answer":"supplied model answer","reference":"reference"}
    assert "human_label" not in str(client.chat.completions.create.call_args)
    assert "human_note" not in str(client.chat.completions.create.call_args)


@pytest.mark.parametrize("label",[True,"1",2,None])
def test_binary_rejects_invalid_labels(label):
    client=Mock()
    client.chat.completions.create.return_value=SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=json.dumps({"label":label,"reasoning":"r"})))])
    with pytest.raises(ValueError):
        judge_binary("Q","A","R",client=client)


def test_percentile_method_and_single_sample():
    assert percentiles([1,3])=={"p50":2,"p95":2.9,"p99":2.98}
    assert percentiles([4])=={"p50":4,"p95":4,"p99":4}
    with pytest.raises(ValueError):
        percentiles([])


@pytest.fixture
def guard_report():
    attacks,clean,outputs=[read_json(p) for p in (ADVERSARIAL_SET_PATH,CLEAN_SET_PATH,OUTPUT_SET_PATH)]
    def group(source):
        rows=[{**r,"actual":r["expected"],"passed":True,
               "blocked_by":"nemo_input" if r["expected"]=="blocked" else None} for r in source]
        return {"total":len(rows),"passed":len(rows),"pass_rate":1,"results":rows}
    clean_group=group(clean)
    clean_group["false_positive_rate"]=0
    output_rows=[{**r,"safe":r["expected"]=="safe","passed":True,
                  "final_answer":r["answer"] if r["expected"]=="safe" else "refusal",
                  "flagged_reason":None if r["expected"]=="safe" else "sensitive"} for r in outputs]
    latency=summarize_latency([{"presidio_ms":1,"nemo_input_ms":3,"input_guard_ms":4} for _ in range(20)])
    meta=metadata([ADVERSARIAL_SET_PATH,CLEAN_SET_PATH,OUTPUT_SET_PATH], models={
        "generation":[],"evaluator":[],"judge":[],"guard":["guard-test"]})
    return {"metadata":meta,"adversarial":group(attacks),"clean":clean_group,"output_results":output_rows,
            "latency":latency},attacks,clean,outputs


def test_guard_valid_evidence(guard_report):
    validate_phase_c(*guard_report)


@pytest.mark.parametrize("mutation", ["missing_metadata", "missing_guard", "wrong_pass_type", "missing_samples"])
def test_guard_schema_rejects_missing_or_wrong_fields(guard_report, mutation):
    report, attacks, clean, outputs = copy.deepcopy(guard_report)
    if mutation == "missing_metadata":
        del report["metadata"]
    elif mutation == "missing_guard":
        del report["metadata"]["models"]["guard"]
    elif mutation == "wrong_pass_type":
        report["output_results"][0]["passed"] = "true"
    else:
        del report["latency"]["samples"]
    with pytest.raises(ValueError, match="phase_c schema"):
        validate_phase_c(report, attacks, clean, outputs)


def test_failed_output_experiment_can_be_saved_but_not_submitted(guard_report):
    report,attacks,clean,outputs=copy.deepcopy(guard_report)
    row=report["output_results"][0]
    row.update(safe=False,passed=False,final_answer="refusal",flagged_reason="false positive")
    validate_phase_c(report,attacks,clean,outputs,require_quality=False)
    with pytest.raises(ValueError,match="output safety"):
        validate_phase_c(report,attacks,clean,outputs)


def test_always_block_cannot_pass(guard_report):
    report,attacks,clean,outputs=copy.deepcopy(guard_report)
    for row in report["clean"]["results"]:
        row.update(actual="blocked",passed=False,blocked_by="nemo_input")
    report["clean"].update(passed=0,pass_rate=0,false_positive_rate=1)
    with pytest.raises(ValueError,match="incorrectly blocked"):
        validate_phase_c(report,attacks,clean,outputs)


@pytest.mark.parametrize("mutation",["empty","false_pass","wrong_count","zero_latency"])
def test_guard_rejects_incomplete_results(guard_report,mutation):
    report,attacks,clean,outputs=copy.deepcopy(guard_report)
    if mutation=="empty":
        report["adversarial"]["results"]=[]
    elif mutation=="false_pass":
        report["adversarial"]["results"][0]["actual"]="allowed"
        report["adversarial"]["results"][0]["blocked_by"]=None
    elif mutation=="wrong_count":
        report["adversarial"]["passed"]=19
    else:
        report["latency"]=summarize_latency([{"presidio_ms":0,"nemo_input_ms":0,"input_guard_ms":0}]*20)
    with pytest.raises(ValueError):
        validate_phase_c(report,attacks,clean,outputs)


@pytest.mark.parametrize("marker",["{{name}}","[Họ Tên]","| ? ms |","| metric | |"])
def test_checker_rejects_markdown_placeholders(tmp_path,marker):
    path=tmp_path/"analysis.md"
    path.write_text("# Report\n"+"Evidence explained. "*20+"\n"+marker+"\n",encoding="utf-8")
    with pytest.raises(ValueError):
        validate_markdown(path)


def test_checker_allows_unmeasured_optional_layers(tmp_path):
    path=tmp_path/"blueprint.md"
    path.write_text("# Blueprint\n"+"Measured input guard only. "*20+
                    "\n| Layer | Result |\n| RAG | chưa đo |\n",encoding="utf-8")
    validate_markdown(path)


def test_phase_b_runner_calibrates_exact_saved_answer(tmp_path,monkeypatch,openai_client):
    from src import experiment_runners as runners,phase_b_judge as phase
    questions=read_json(TEST_SET_PATH)
    humans=read_json(HUMAN_LABELS_PATH)
    answers=[{**q,"answer":"PIPELINE "+str(q["id"]),"contexts":["context"],
              "generation_mode":"llm","generation_model":"generation-test"} for q in questions]
    paths={}
    for name,rows in [("test_set_50q.json",questions),("human_labels_10q.json",humans),("answers_50q.json",answers)]:
        paths[name]=tmp_path/name
        write_json(paths[name],rows)
    monkeypatch.setattr(runners,"TEST_SET_PATH",paths["test_set_50q.json"])
    monkeypatch.setattr(runners,"HUMAN_LABELS_PATH",paths["human_labels_10q.json"])
    monkeypatch.setattr(runners,"ANSWERS_PATH",paths["answers_50q.json"])
    monkeypatch.setattr(runners,"ARTIFACTS_DIR",tmp_path/"artifacts")
    def swap(q,a,b,reference=""):
        assert reference
        return phase.JudgeResult(q,a,b,"A","A","A","first","second",True,
                                 {"A":.9,"B":.2},{"A":.9,"B":.2})
    monkeypatch.setattr(phase,"swap_and_average",swap)
    labels={h["model_answer"]:h["human_label"] for h in humans}
    binary=Mock(side_effect=lambda q,a,r,client=None:{"label":labels[a],"reasoning":"mock reference evaluation"})
    monkeypatch.setattr(runners,"judge_binary",binary)
    monkeypatch.setattr(phase,"cohen_kappa",lambda a,b:1)
    decisive_longer=sum(len(answers[h["question_id"]-1]["answer"])>len(h["model_answer"])
                        for h in humans if h["question_id"] in runners.PAIR_QUESTION_IDS)
    monkeypatch.setattr(phase,"bias_report",lambda results:{
        "total_judged":5,"position_bias_count":0,"position_bias_rate":0,
        "verbosity_bias":decisive_longer/5,"interpretation":"mock interpretation",
        "verbosity_details":{"a_wins_a_longer":decisive_longer,"b_wins_b_longer":0,"total_decisive":5}})
    report=runners.run_phase_b()
    assert binary.call_count==10 and len(report["pairwise_results"])==5
    assert [call.args[1] for call in binary.call_args_list]==[h["model_answer"] for h in humans]
    assert all(call.kwargs == {"client":openai_client} for call in binary.call_args_list)
    assert (tmp_path/"artifacts/judge_results.json").is_file()


def test_checker_does_not_run_pytest_or_api_by_default(tmp_path,monkeypatch):
    from scripts import check_lab
    runner=Mock(side_effect=AssertionError("Unexpected subprocess/API"))
    monkeypatch.setattr(check_lab.subprocess,"run",runner)
    assert check_lab.main(["--root",str(tmp_path)])==1
    runner.assert_not_called()

def test_schema_documents_are_valid():
    from jsonschema import Draft202012Validator
    for path in Path("doc/schemas").glob("*.json"):
        Draft202012Validator.check_schema(read_json(path))


def test_phase_c_runner_executes_one_input_batch_and_four_outputs(tmp_path,monkeypatch):
    from src import experiment_runners as runners,phase_c_guard as phase
    from src import llm_client
    monkeypatch.setattr(runners,"ARTIFACTS_DIR",tmp_path)
    from unittest.mock import AsyncMock
    monkeypatch.setattr(llm_client,"pace_llm_request",AsyncMock())
    monkeypatch.setattr(phase,"setup_presidio",lambda:(object(),object()))
    models=iter(["guard-input","guard-output","guard-latency"])
    monkeypatch.setattr(phase,"setup_nemo_rails",lambda:SimpleNamespace(config=SimpleNamespace(
        models=[SimpleNamespace(type="main",model=next(models))])))
    def batch(inputs,**kwargs):
        return [{**item,"actual":item["expected"],"passed":True,
                 "blocked_by":"nemo_input" if item["expected"]=="blocked" else None} for item in inputs]
    batched=Mock(side_effect=batch)
    monkeypatch.setattr(phase,"run_adversarial_suite",batched)
    cases={row["answer"]:row for row in read_json(OUTPUT_SET_PATH)}
    async def output(q,a,rails=None):
        safe=cases[a]["expected"]=="safe"
        return {"safe":safe,"flagged_reason":None if safe else "sensitive",
                "final_answer":a if safe else "refusal"}
    checked=AsyncMock(side_effect=output)
    monkeypatch.setattr(phase,"check_output_rail",checked)
    latency=Mock(side_effect=lambda inputs,n_runs,**kwargs:summarize_latency(
        [{"presidio_ms":1,"nemo_input_ms":3,"input_guard_ms":4}]*n_runs))
    monkeypatch.setattr(phase,"measure_p95_latency",latency)
    report=runners.run_phase_c()
    assert batched.call_count==1 and len(batched.call_args.args[0])==28
    assert batched.call_args.kwargs["pace_requests"] is True
    assert checked.await_count==4 and latency.call_count==1
    assert latency.call_args.kwargs["pace_requests"] is True
    assert llm_client.pace_llm_request.await_count==4
    assert report["clean"]["false_positive_rate"]==0
    assert report["metadata"]["models"]=={
        "generation":[],"evaluator":[],"judge":[],
        "guard":["guard-input","guard-latency","guard-output"]}
    assert (tmp_path/"guard_results.json").is_file()


def test_team_requires_every_individual_entry(tmp_path):
    from src.report_contracts import validate_team
    path=tmp_path/"TEAM.md"
    content="# Team\n"+"Contribution evidence. "*20+"""
| STT | Name | MSSV | Work |
|---|---|---|---|
| 1 | A | A01 | phase A |
| 2 | B | B02 | phase B |
## INDIVIDUAL
### A-A01
Evidence.
"""
    path.write_text(content,encoding="utf-8")
    with pytest.raises(ValueError,match="B02"):
        validate_team(path)
    path.write_text(content+"\n### B-B02\nEvidence.",encoding="utf-8")
    validate_team(path)


def test_setup_preserves_metadata_and_does_not_call_pipeline_py(monkeypatch):
    from scripts import setup_answers
    import sys
    children=[SimpleNamespace(text="raw",metadata={"source":"policy"},parent_id="parent")]
    search=SimpleNamespace(index=Mock(),search=Mock())
    reranker=object()
    monkeypatch.setitem(sys.modules,"src.m1_chunking",SimpleNamespace(
        load_documents=lambda:[{"text":"document","metadata":{"source":"policy"}}],
        chunk_hierarchical=lambda text,metadata:([],children)))
    monkeypatch.setitem(sys.modules,"src.m2_search",SimpleNamespace(HybridSearch=lambda:search))
    monkeypatch.setitem(sys.modules,"src.m3_rerank",SimpleNamespace(CrossEncoderReranker=lambda:reranker))
    monkeypatch.setitem(sys.modules,"src.m5_enrichment",SimpleNamespace(
        enrich_chunks=lambda chunks:[SimpleNamespace(enriched_text="enriched",auto_metadata={"topic":"HR"})]))
    monkeypatch.setitem(sys.modules,"src.pipeline",SimpleNamespace(
        run=Mock(side_effect=AssertionError("Must not call pipeline.py"))))
    returned=setup_answers.build_pipeline()
    assert returned[:2]==(search,reranker)
    chunk=search.index.call_args.args[0][0]
    assert chunk=={"text":"enriched","metadata":{"source":"policy","parent_id":"parent","topic":"HR"}}


def test_setup_generation_accepts_reused_client():
    from scripts import setup_answers
    search=SimpleNamespace(search=lambda q:[SimpleNamespace(text="context",score=.8,metadata={})])
    reranker=SimpleNamespace(rerank=lambda q,docs,top_k:[SimpleNamespace(text="context")])
    client=Mock()
    client.chat.completions.create.return_value=SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content="generated answer"))])
    answer,contexts,mode,model=setup_answers.run_query("Q",search,reranker,3,client)
    assert (answer,contexts,mode,model)==("generated answer",["context"],"llm",setup_answers.GENERATION_MODEL)
    client.chat.completions.create.assert_called_once()
