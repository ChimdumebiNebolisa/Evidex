"""Cross-file coverage, selection reproduction and source-lineage checks."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import random

A=Path(__file__).resolve().parent
E=A.parents[1]
F=E/'reports/full3-final-2026-10-17T13-43-20.656767+00-00'


def csv_rows(name):
    with (A/name).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))


case=csv_rows('COMPARISON_CASES.csv');outcome=csv_rows('OUTCOME_SUMMARY.csv')
assert len(case)==60000 and len({(r['claim_id'],r['model'],r['contrast']) for r in case})==60000
groups=collections.defaultdict(list)
for r in case:
    assert sum(int(r[g]) for g in ('stayed_correct','rescue','regression','stayed_wrong'))==3
    for g in ('stayed_correct','rescue','regression','stayed_wrong'):
        assert int(r[g])==sum(r['r'+str(k)]==g for k in (1,2,3))
    groups[r['model'],r['contrast']].append(r)
for (model,contrast),rs in groups.items():
    assert len(rs)==10000
    os=[r for r in outcome if r['model']==model and r['contrast']==contrast]
    for rep in (1,2,3):
        subset=[r for r in os if r['row_type']=='by_repetition' and r['repetition']==str(rep)]
        assert sum(int(r['comparison_count']) for r in subset)==10000
        for row in subset:assert int(row['comparison_count'])==sum(r['r'+str(rep)]==row['outcome'] for r in rs)
    patterns=[r for r in os if r['row_type']=='within_claim_pattern']
    assert sum(int(r['distinct_claim_count']) for r in patterns)==10000
    for row in [r for r in os if r['row_type']=='all_repetitions']:
        assert int(row['comparison_count'])==sum(int(r[row['outcome']]) for r in rs)
        assert int(row['distinct_claim_count'])==sum(int(r[row['outcome']])>0 for r in rs)
sample=csv_rows('TAXONOMY_SAMPLE.csv');taxonomy=csv_rows('TAXONOMY_CASES.csv');eligibility=csv_rows('SAMPLE_GROUPS.csv')
assert len(taxonomy)==len(sample)==465 and {r['case_id'] for r in taxonomy}=={r['case_id'] for r in sample}
assert len({r['claim_id'] for r in taxonomy})==416
by_key={(r['claim_id'],r['model'],r['contrast']):r for r in case}
for row in eligibility:
    model,contrast=row['model'],row['contrast'];route=row['group'].split('/',1)[1]
    eligible=[r['claim_id'] for r in groups[model,contrast] if (int(r['regression'])==3 if route.endswith('regression_all3') else 0<int(r['regression'])<3 if route.endswith('some_not_all') else r['r1']==route.removeprefix('AB_firstpass_'))]
    eligible=sorted(eligible)
    assert len(eligible)==int(row['eligible_model_claim_cases'])
    seed=int.from_bytes(hashlib.sha256(f'20261017|{model}|{route}'.encode()).digest()[:8],'big')
    assert seed==int(row['group_seed'])
    expected=set(eligible) if row['cap']=='all' else set(random.Random(seed).sample(eligible,min(int(row['cap']),len(eligible))))
    actual={r['claim_id'] for r in sample if row['group'] in r['selection_flags'].split(';')}
    assert expected==actual and len(actual)==int(row['selected_model_claim_cases'])
inputs={r['claim_id']:r for r in map(json.loads,(E/'prepared/inputs.jsonl').read_text(encoding='utf8').splitlines())}
pred={(r['claim_id'],r['model'],r['condition'],r['repetition']):r['label'] for r in map(json.loads,(F/'OUTCOMES.jsonl').read_text().splitlines())}
response_paths=json.loads((F/'RESPONSE_HASHES.json').read_text())
cb=json.loads((A/'CODEBOOK_FREEZE.json').read_text());assert hashlib.sha256((A/'REGRESSION_CODEBOOK.md').read_bytes()).hexdigest()==cb['codebook_sha256']
for r in taxonomy:
    source=inputs[r['claim_id']]
    assert r['claim_text']==source['claim_text'] and r['complete_supplied_evidence']==source['gold_evidence'] and r['reference_label']==source['gold_label']
    assert r['review_status']=='AI-coded_unblinded; human_review_not_performed'
    assert r['evidence_reference_assessment'] in cb['alignment']
    for c in 'ABC':
        for rep in (1,2,3):assert r[f'{c}_r{rep}']==pred[r['claim_id'],r['model'],c,rep]
    pair=by_key[r['claim_id'],r['model'],r['contrast']]
    assert [r['r'+str(rep)+'_outcome'] for rep in (1,2,3)]==[pair['r'+str(rep)] for rep in (1,2,3)]
    for p in json.loads(r['source_response_records']):assert Path(p).relative_to(E/'runs/full3').as_posix() in response_paths
    assert r['codebook_sha256']==cb['codebook_sha256']
var=csv_rows('IDENTICAL_PROMPT_VARIABILITY.csv')
assert len(var)==60000
for r in var:
    labels=[r['r'+str(k)] for k in (1,2,3)];g=inputs[r['claim_id']]['gold_label'];correct=[x==g for x in labels]
    d=sum(labels[i]!=labels[j] for i,j in ((0,1),(0,2),(1,2)))
    loss=sum(correct[i] and not correct[j] for i in range(3) for j in range(3) if i!=j)
    assert int(r['disagreeing_unordered_pairs'])==d and int(r['directional_correct_to_wrong_ordered_pairs'])==loss
    assert abs(float(r['disagreement_fraction'])-2*float(r['directional_loss_fraction']))<1e-12
rec=json.loads((A/'PILOT_RECODE.json').read_text())
assert hashlib.sha256((A/'annotations_pilot.tsv').read_bytes()).hexdigest()==rec['final_annotations_sha256']
selection_freeze=json.loads((A/'SELECTION_FREEZE.json').read_text())
for name,h in selection_freeze['sample_files_sha256'].items():assert hashlib.sha256((A/name).read_bytes()).hexdigest()==h
result={'status':'PASS','all_model_claim_contrast_vectors':len(case),'complete_summary_rows':len(outcome),'identical_prompt_cells':len(var),'selected_cases_checked':len(taxonomy),'selected_distinct_claims_checked':416,'selection_groups_reproduced':len(eligibility),'case_text_and_reference_equal_frozen_inputs':True,'case_predictions_equal_frozen_outcomes':True,'source_response_paths_match_inventory':True,'unchanged_selection_and_codebook_freezes':True,'pilot_recode_hash_valid':True,'limits':'Structural/numerical/source checks do not constitute independent human validation of interpretive feature/alignment judgments'}
with (A/'TAXONOMY_CHECKS.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
