"""Write isolated Cursor judge packets (rubric + blinded items only).

Packets contain no GLM judgments, FEVER labels, GPT predictions, cohort
labels, NLI scores, or Analysis v2 features. Used by isolated judge agents.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import run_judges  # noqa: E402

STAGE_FILE = run_judges.STAGE_FILE


def load_blinded(stage: str):
    src = config.BLINDED_DIR / STAGE_FILE[stage]
    recs = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["item_id"]: r for r in recs}


def missing_batches(stage: str, judge: str):
    expected = run_judges.expected_items(stage)
    done, _ = run_judges.judge_status(stage, judge)
    missing = [i for i in expected if i not in done]
    batches = []
    for start in range(0, len(missing), config.BATCH_SIZE):
        chunk = missing[start:start + config.BATCH_SIZE]
        if chunk:
            batches.append(chunk)
    return batches


def write_packets(stage: str):
    if config.PANEL != "cursor":
        raise SystemExit("prepare_packets is Cursor-panel only; pass --panel cursor")
    config.require_locked_model(config.LOCKED_MODEL)
    config.ensure_dirs()
    blinded = load_blinded(stage)
    rubric = (config.PROMPTS_DIR / "judge_rubric.md").read_text(encoding="utf-8")
    protocol = (config.PROMPTS_DIR / "progressive_disclosure_protocol.md").read_text(
        encoding="utf-8")
    outdir = config.CURSOR_PANEL_ROOT / "cache" / "packets" / f"stage_{stage.lower()}"
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for judge in config.JUDGES:
        for i, item_ids in enumerate(missing_batches(stage, judge), start=1):
            items = [blinded[iid] for iid in item_ids]
            batch_name = f"{judge}_batch_{i:02d}"
            out_rel = (
                Path("silver_adjudication_v1/cursor_panel/judgments")
                / f"stage_{stage.lower()}" / f"{batch_name}.jsonl"
            )
            packet = {
                "judge_id": judge,
                "stage": stage,
                "model": config.LOCKED_MODEL,
                "output_path": out_rel.as_posix(),
                "n_items": len(items),
                "item_ids": item_ids,
                "items": items,
                "rubric": rubric,
                "disclosure_note": (
                    f"This is Stage {stage}. Use only the fields in each item. "
                    "Do not browse, look up facts, or read other repository files."
                ),
            }
            path = outdir / f"{batch_name}.json"
            path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            written.append({"judge": judge, "batch": batch_name, "n": len(items),
                            "packet": path.as_posix(), "output": out_rel.as_posix()})
    manifest = config.CURSOR_PANEL_ROOT / "cache" / f"queue_stage_{stage}.json"
    manifest.write_text(json.dumps(written, indent=2), encoding="utf-8")
    print(f"Stage {stage}: wrote {len(written)} packets -> {outdir}")
    return written


if __name__ == "__main__":
    stage = sys.argv[1].upper() if len(sys.argv) > 1 else "A"
    if stage not in config.STAGES:
        raise SystemExit(f"invalid stage {stage}")
    write_packets(stage)
