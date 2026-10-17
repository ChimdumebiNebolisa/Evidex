"""Create review documents and compare historical bytes; never launch inference."""
import importlib.metadata
import json
import math
import platform
import subprocess
from pathlib import Path
from common import HERE, ROOT, digest, load, now, write_new

def main():
    cost=load(HERE/'COST_ESTIMATE.json')
    lines=['# Cost estimate — October 16, 2026','',
           'Prepared-prompt estimate for direct OpenAI global standard Chat Completions. Currency: USD. No paid requests have been made.','',
           '| Design | Planned calls | Two-token label scenario | With 10% extra attempts | 32-token cap + 10% extra attempts | Three-attempt cap scenario |',
           '|---|---:|---:|---:|---:|---:|']
    for row in cost['designs']:
        lines.append(f"| {row['design']} | {row['calls']:,} | ${row['expected_usd']:.4f} | ${row['expected_with_10_percent_extra_attempts_usd']:.4f} | ${row['output_cap_with_10_percent_extra_attempts_usd']:.4f} | ${row['three_attempt_policy_envelope_usd']:.4f} |")
    lines+=['', 'The recommended full3 plan costs about **$24.75** when replies are stand-alone labels, or **$27.22** in the 10% extra-attempt scenario. These are estimates, not an approved budget or a billing guarantee. A 32-token output cap is not an assertion that 32 tokens will be generated. Retry scenarios are allowances, not measured service-failure probabilities. The 12-call smoke adds about $0.0018 under the two-token scenario; it remains paid inference.','',
      '## Verified rates and route','',
      '[Official OpenAI pricing](https://developers.openai.com/api/docs/pricing), standard text-token table, checked October 16, 2026: GPT-5.4 input $2.50 / output $15.00 per million; GPT-5.4-mini input $0.75 / output $4.50. No Batch, caching, regional, priority, tool or subscription discount is used. The plan requests global standard service. No browsing/tools are configured. Taxes and account credits are not estimated.','',
      '[GPT-5.4 model documentation](https://developers.openai.com/api/docs/models/gpt-5.4) and [GPT-5.4-mini documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini) list the original aliases, none reasoning effort and Chat Completions support. Actual account entitlement and completion parameter acceptance are pending. No key was available at build time.','',
      '## Token calculation','',
      '`tiktoken==0.12.0`, `o200k_base`, counts each complete substituted message content. Totals per one model and one full pass: A 331,901; B 788,053; C 848,053 content tokens. Add an estimated seven framing/role/priming tokens per single-user request: 2,178,007 estimated input tokens for 30,000 calls per model. Stand-alone Supported/Refuted labels require at most two local tokens, so the label scenario charges two output tokens on every call. The price calculation uses every actual subset message too; it does not multiply an unrelated average length.','',
      'Formula per model: `(estimated input tokens × input rate + calls × output tokens × output rate) / 1,000,000`. The full3 input estimate is 6,534,021 per model, and 90,000 completions per model.','',
      'Actual service-side token framing, cache behavior and usage can differ. The runner explicitly requests none reasoning, and `max_completion_tokens=32` caps visible plus reasoning tokens where supported. Any reported reasoning tokens are billed at the output rate and retained. The smoke test must calibrate actual usage and verify settings before the full run. The maximum-attempt cost column assumes every logical job incurs all three attempts and each attempt is charged the estimated input plus the full output cap; this is a conservative scenario, not a guaranteed upper bill. All attempts and missing usage remain visible.','',
      '## Precision tradeoff','',
      'At an assumed 1% rate, a 2,000-record repeated subset contains about 20 events, with a planning Wilson interval about 0.65–1.54%. At 10,000 records, about 100 events gives 0.82–1.21%. Neither replication counts nor conditional repeated pairs create additional independent claims. Under an illustrative paired discordance q=0.02, 95% half-widths are approximately 0.62 pp versus 0.28 pp. These approximations do not establish power and do not include all clustering/provider uncertainty.','',
      '**Recommendation:** three fresh repetitions across all 10,000 claims (full3), after an approved 12-call smoke test. The $13.23 difference from hybrid3 buys repeat measurements on the full target sample and avoids a much less precise rare-regression repeat estimate. Five repetitions cost more without expanding the number of claim clusters.']
    (HERE/'COST_ESTIMATE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'RUN_MATRIX.csv').write_text('design,planned_calls,expected_usd,expected_with_10_percent_extra_attempts_usd\n'+'\n'.join(f"{r['design']},{r['calls']},{r['expected_usd']:.8f},{r['expected_with_10_percent_extra_attempts_usd']:.8f}" for r in cost['designs'])+'\n',encoding='utf-8')
    snapshot=load(Path(r'C:/Users/Chimdumebi/evidex-stage2-audits/2026-10-16-6f57f49337/initial-snapshot.json'))
    changed=[name for name,meta in snapshot['files'].items() if not (ROOT/name).is_file() or digest(ROOT/name)!=meta['sha256'] or (ROOT/name).stat().st_size!=meta['size']]
    tracked=subprocess.check_output(['git','diff','--binary'],cwd=ROOT,text=True)
    staged=subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT,text=True)
    current_files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    added=[p for p in current_files if p and p not in snapshot['files']]
    unexpected=[p for p in added if not p.startswith('replacement_predictor_v1/')]
    record={'checked_at_utc':now(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
      'sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'historical_files_checked':len(snapshot['files']),'historical_files_changed':changed,'unexpected_new_files':unexpected,
      'preexisting_untracked_files':778,'old_status_reference':'Stage 2 initial snapshot, same SHA; all inventoried historical bytes checked now',
      'tracked_diff_unchanged':tracked==snapshot['diff'],'staged_diff_unchanged':staged==snapshot['cached_diff'],
      'new_files':added,'python':platform.python_version(),
      'dependency_versions':{x:importlib.metadata.version(x) for x in ['numpy','pytest']},
      'tokenizer':'tiktoken==0.12.0 installed in replacement_predictor_v1/.deps; no global install',
      'public_model_listing_verified':True,'account_access':'unverified; no key in process/user/machine environment',
      'paid_inference_calls':0,'judging_calls':0}
    (HERE/'PRESERVATION.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    if changed or unexpected or not record['tracked_diff_unchanged'] or not record['staged_diff_unchanged']:
        raise SystemExit('Historical preservation failed; inspect PRESERVATION.json')
    print(json.dumps({'historical_files_checked':len(snapshot['files']),'historical_changes':len(changed),'new_files':len(added),'unexpected_new_files':len(unexpected)}))

if __name__=='__main__':main()
