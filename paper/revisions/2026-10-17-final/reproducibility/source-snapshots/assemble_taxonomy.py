"""Assemble manually read/coded records and transparently count selected groups."""
import collections
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

A=Path(__file__).resolve().parent
E=A.parents[1]
F=E/'reports/full3-final-2026-10-17T13-43-20.656767+00-00'
freeze=json.loads((A/'CODEBOOK_FREEZE.json').read_text())
assert hashlib.sha256((A/'REGRESSION_CODEBOOK.md').read_bytes()).hexdigest()==freeze['codebook_sha256']
annotations={};annotation_sources={}
for p in sorted(A.glob('annotations_*.tsv')):
    for row in csv.DictReader(p.open(encoding='utf8'),delimiter='\t'):
        assert row['claim_id'] not in annotations
        assert set(row['categories'].split(';'))<=set(freeze['codes'])
        assert row['alignment'] in freeze['alignment']
        assert row['categories']=='DIRECT' or 'DIRECT' not in row['categories'].split(';')
        annotations[row['claim_id']]=row;annotation_sources[row['claim_id']]=p.name
claims={r['claim_id']:r for r in map(json.loads,(A/'SELECTED_CLAIM_RECORDS.jsonl').read_text(encoding='utf8').splitlines())}
assert len(claims)==len(annotations)==416 and set(claims)==set(annotations)
sample=list(csv.DictReader((A/'TAXONOMY_SAMPLE.csv').open(encoding='utf8')))
raw={o['job_id']:o for o in map(json.loads,(F/'OUTCOMES.jsonl').read_text().splitlines())}
rows=[]
input_hash=hashlib.sha256((E/'prepared/inputs.jsonl').read_bytes()).hexdigest()
for selected in sample:
    cid=selected['claim_id'];claim=claims[cid];annotation=annotations[cid];model=selected['model'];contrast=selected['contrast']
    preds=claim['predictions'][model]
    paths=[]
    for c in contrast:
        for rep in (1,2,3):
            job=f'{cid}_{model}_{c}_r{rep:02d}';o=raw[job]
            ordinal=2 if o['attempt_directories']==2 else 1
            paths.append(str(E/'runs/full3/attempts'/job/f'attempt-{ordinal:02d}'/'response.bin'))
    interpretation={'supports_gold':'Benchmark errors are apparent prediction errors under the ordinary supplied-text reading; the feature codes do not identify an internal mechanism.','conflicts_gold':'Benchmark-defined errors/rescues coexist with apparent reference tension; do not identify real-world correctness or repair the frozen score.','insufficient':'Benchmark-defined outcomes are retained, but the selected evidence does not settle a material proposition; no model mechanism is established.','ambiguous':'Benchmark-defined outcomes are retained; competing reasonable text readings prevent a unique explanation of the scored change.'}[annotation['alignment']]
    rows.append({**selected,'claim_text':claim['claim_text'],'complete_supplied_evidence':claim['gold_evidence'],'reference_label':claim['gold_label'],'A_r1':preds['A'][0],'A_r2':preds['A'][1],'A_r3':preds['A'][2],'B_r1':preds['B'][0],'B_r2':preds['B'][1],'B_r3':preds['B'][2],'C_r1':preds['C'][0],'C_r2':preds['C'][1],'C_r3':preds['C'][2],'categories':annotation['categories'],'evidence_reference_assessment':annotation['alignment'],'justification':annotation['justification'],'annotation_confidence':annotation['confidence'],'uncertainty':interpretation,'review_status':'AI-coded_unblinded; human_review_not_performed','human_review_priority':'high' if annotation['alignment']!='supports_gold' or annotation['confidence']=='low' else 'routine','source_response_records':json.dumps(paths),'source_input_sha256':input_hash,'feature_annotation_source':annotation_sources[cid],'pilot_recoded':str(claim['pilot']),'codebook_sha256':freeze['codebook_sha256'],'model_reasoning_evidence':'None collected: label-only predictions; explanations are analyst hypotheses.'})
assert len(rows)==len({r['case_id'] for r in rows})==465
with (A/'TAXONOMY_CASES.csv').open('x',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
cohorts=('AB_regression_all3','BC_regression_all3','AB_firstpass_rescue','AB_firstpass_stayed_wrong','AB_firstpass_stayed_correct','AB_regression_some_not_all')
aggregates={};category_rows=[]
for cohort in cohorts:
    rs=[r for r in rows if any(x.endswith('/'+cohort) for x in r['selection_flags'].split(';'))]
    group={'cases':len(rs),'distinct_claims':len({r['claim_id'] for r in rs}),'alignment':dict(collections.Counter(r['evidence_reference_assessment'] for r in rs)),'categories':dict(collections.Counter(code for r in rs for code in r['categories'].split(';'))),'model_counts':dict(collections.Counter(r['model'] for r in rs))}
    aggregates[cohort]=group
    for code in freeze['codes']:
        category_rows.append({'selected_group':cohort,'category':code,'selected_case_denominator':len(rs),'case_count':sum(code in r['categories'].split(';') for r in rs),'selected_distinct_claim_denominator':len({r['claim_id'] for r in rs}),'distinct_claim_count':len({r['claim_id'] for r in rs if code in r['categories'].split(';')}),'population_prevalence_estimate':False})
with (A/'CATEGORY_COUNTS.csv').open('x',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(category_rows[0]));w.writeheader();w.writerows(category_rows)
# Full-dataset cohort identities are separate from the deliberately selected taxonomy sample.
comparison=list(csv.DictReader((A/'COMPARISON_CASES.csv').open(encoding='utf8')))
full={}
for contrast in ('AB','BC','AC'):
    rs=[r for r in comparison if r['contrast']==contrast]
    full[contrast]={}
    for label,predicate in [('firstpass_regression',lambda r:r['r1']=='regression'),('any_repeat_regression',lambda r:int(r['regression'])>0),('all3_regression',lambda r:int(r['regression'])==3)]:
        selected=[r for r in rs if predicate(r)]
        ids_by_model={m:{r['claim_id'] for r in selected if r['model']==m} for m in ('gpt-5.4','gpt-5.4-mini')}
        full[contrast][label]={'model_claim_cases':len(selected),'distinct_claims':len({r['claim_id'] for r in selected}),'both_models':len(set.intersection(*ids_by_model.values())),'per_model':{m:len(v) for m,v in ids_by_model.items()}}
hist={r['claim_id'] for r in map(json.loads,(E/'prepared/inputs.jsonl').read_text(encoding='utf8').splitlines()) if r['historical_regression']}
fresh={r['claim_id'] for r in comparison if r['contrast']=='AB' and int(r['regression'])==3}
full['historical226_overlap_with_fresh_all3_AB']={'historical_claims':len(hist),'fresh_claims':len(fresh),'intersection':len(hist&fresh)}
with (A/'TAXONOMY_AGGREGATES.json').open('x',encoding='utf8') as f:
    json.dump({'selected_cohorts':aggregates,'full_dataset_recurring':full,'unique_claim_assessments':dict(collections.Counter(r['alignment'] for r in annotations.values())),'unique_claim_feature_counts':dict(collections.Counter(c for r in annotations.values() for c in r['categories'].split(';')))},f,indent=2)

lines=['# Exploratory taxonomy of comparison outcomes','',
 'This is a selected, post-result case study. All 465 selected model–claim–contrast cases were coded, reusing feature annotations across 416 distinct claims. Full supplied evidence and all three A/B/C predictions were read for each claim. The 30-case pilot was documented, definitions frozen, and pilot recoded before the other 386 claims. Coding was by one AI analyst, unblinded to outcomes; no human review, independent coder or agreement statistic exists. No experimental predictor/judge calls were made.','',
 'The frozen reference labels and all quantitative scores are unchanged. Apparent reference conflicts are text-review flags, not validated benchmark corrections.','',
 '## Sample and denominators','',
 '| Selection group | Selected model–claim–contrast cases | Distinct claims | Per-model cases (5.4 / mini) |',
 '|---|---:|---:|---|']
for group in cohorts:
    x=aggregates[group]
    lines.append(f'| {group} | {x["cases"]} | {x["distinct_claims"]} | {x["model_counts"].get("gpt-5.4",0)} / {x["model_counts"].get("gpt-5.4-mini",0)} |')
lines+=['','The 186 recurring A→B cases are 87 + 99 model–claim observations, overlapping on 26 claims: 160 distinct claims. The historical manuscript’s 186 model-specific claims had a different definition and must not be substituted. SAMPLE_GROUPS.csv records all twelve eligible populations, caps and derived group seeds; master seed 20261017. TAXONOMY_SAMPLE.csv records every selected case and flag. Selection was without replacement within each group; case deduplication is by claim/model/contrast, and claim-level annotations are reused across models/contrasts. The cohorts deliberately overrepresent recurring regressions and contain sampled controls. Category counts/proportions cannot estimate prevalence in all 10,000 claims.','',
 '## Apparent evidence/reference alignment','',
 '| Selected group | Supports frozen reference | Apparent conflict with reference | Selected evidence insufficient | Ambiguous reading | Case denominator |',
 '|---|---:|---:|---:|---:|---:|']
for group in cohorts:
    x=aggregates[group];c=x['alignment']
    lines.append(f'| {group} | {c.get("supports_gold",0)} | {c.get("conflicts_gold",0)} | {c.get("insufficient",0)} | {c.get("ambiguous",0)} | {x["cases"]} |')
lines+=['','At the distinct-claim level across this selected sample, there are 213 supports-reference assessments, 43 apparent conflicts, 90 insufficient-evidence assessments and 70 ambiguous readings (denominator 416). These are AI-assisted coding judgments, not human-validated labels or dataset-wide error rates. A conflict is stronger than missing support: for example, 51757 supplies “KGB was a military service” against a frozen Supported claim saying it was not. In 103003 the actress biography merely omits the claimed TV appearance; that is insufficiency, not proof of a wrong reference.','',
 '## Observable feature counts across selected groups','',
 'Counts below use model–claim–contrast cases; multiple feature codes are allowed. Columns use the case denominators in the sample table and are not independent populations. The distinct-claim counts and denominators for every cell are in CATEGORY_COUNTS.csv.','',
 '| Code | AB all-three regression (186) | BC all-three regression (59) | AB rescue (60) | AB stayed wrong (60) | AB stayed correct (60) | AB mixed regression (40) |',
 '|---|---:|---:|---:|---:|---:|---:|']
code_names={'NEG':'polarity','SCOPE':'scope/degree','REL':'relation/role','ENT':'entity/attribute','NUM':'number/time','LEX':'semantic reading','CTX':'context/linkage','GAP':'missing warrant','TXT':'wording ambiguity','DIRECT':'direct match','UNCLEAR':'unclear'}
for code in freeze['codes']:
    lines.append('| '+code+' ('+code_names[code]+') | '+' | '.join(str(aggregates[g]['categories'].get(code,0)) for g in cohorts)+' |')
lines+=['','## Comparisons and actual examples','',
 '- **Role/direction and entity binding:** 165882 changes written by to evidence saying portrayed by; mini regresses on A→B in all three calls. The same broad REL demand succeeds in 56381, where both predictors reject uncle in favor of the supplied parent/casting relation. REL therefore identifies a comparison demand, not a sufficient explanation of regression.','- **Numbers and temporal scope:** 218245 is a sampled rescue with an explicit 13th/16th rank mismatch. In 180726, both models change toward the supplied chart peak 6 while the frozen Supported claim says 8: that is still a benchmark regression, but cannot simply be called evidence making the answer factually worse. Exact counts, lower bounds, subintervals and event dates must be distinguished.','- **Polarity:** 129011 gives a clear negative album/artist proposition where main-model B disagrees with supplied text and reference. Conversely, 75904 is rescued after a negated >80% claim is confronted with evidence. And 51757 has an apparent reference conflict. One polarity code spans all three situations.','- **Context:** 89458 leaves the evidence subject as It; main regresses in B while mini remains correct and main recovers in C. In 126590 the similarly implicit It/elevator statement succeeds for both models. A pronoun by itself does not show unusable evidence or a processing mechanism.','- **Paraphrase and granularity:** 164996 correctly generalizes marine mammals to mammals, while 208906’s song-to-work-of-art generalization is scored worse in C. 114093 is a mini rescue on fiction/non-fiction. Semantic category demands occur in both benefits and losses.','- **Insufficient supplied text:** 103003 provides no television appearance; 174893 gives a building location but no demolition; 64142 mixes a sales total with digital-album ranking without identifying a digital-only count. Stricter evidence-only C can change benchmark agreement in such cases without demonstrating degraded reasoning. This concerns the selected evidence actually supplied, not every possible FEVER evidence set.','- **Malformed or unresolved wording:** 92419’s national pain cannot be given a reliable symptom interpretation. It retains UNCLEAR, low confidence and a human-review flag rather than an invented explanation. Scalar barely and ambiguous release/genre/name language remain explicit uncertainty.','',
 'These are hypotheses about visible claim/evidence relationships. No response contains a reasoning trace establishing attention capture, knowledge override, distraction, anchoring, hallucination or a permanent failure mechanism. Feature overlap with rescues/successes limits explanatory specificity. This selected sample does not estimate feature prevalence, odds ratios or causal effects.','',
 '## Reading the quantitative and historical records','',
 'OUTCOME_SUMMARY.csv covers all valid A→B/B→C/A→C pairs by model and repetition, all-repetition counts with distinct-claim unions, and within-claim four-outcome count patterns. COMPARISON_CASES.csv has every one of the 60,000 model–claim–contrast vectors. IDENTICAL_PROMPT_VARIABILITY.csv separately records all 60,000 claim/model/condition repeated-prompt cells, with three unordered label pairs and six ordered directional-loss pairs. Neither label disagreement nor the selected taxonomy is a replacement for the directional-loss estimand.','',
 'The all-three summary includes repetition 1; it is not an independent replication of first-pass results. Recurrent across three calls is a finite observation, not a permanent individual property. The historical 226-case judge cohorts and NLI diagnostics are not automatically analyses of these fresh regressions. Manuscript planning is in MANUSCRIPT_REVISION_PLAN.md; no manuscript has been edited.','',
 '## Reproducibility and review status','',
 'REGRESSION_CODEBOOK.md gives definitions, exclusions, overlap rules, examples and inference limits. CODEBOOK_FREEZE.json and PILOT_RECODE.json establish the recorded coding sequence. annotations_*.tsv retain per-claim analyst judgments and justifications. TAXONOMY_CASES.csv includes complete supplied text, frozen labels/predictions, case-specific limits, input line/hash, raw response paths, confidence and human-review status. No claim is excluded or relabeled in frozen analysis. A next review should prioritize apparent conflicts, insufficiency, ambiguity and low confidence; human review remains unperformed.','',
 'FUNCTIONAL-COMPLETENESS RETROSPECTIVE: selected record coverage complete; coding definitions unchanged; all comparison groups and models represented; feature and reference-assessment axes separate; uncertainty preserved; no human/agreement or mechanism claim. This is ready as an exploratory AI-assisted audit attachment, not as a validated causal taxonomy.','']
boundary='Claim 98108 is also a useful boundary case: the evidence explicitly identifies Honeymoon as a major-label record, yet main-model B disagrees in all three calls while A and C agree with the reference. It is coded DIRECT because no distinctive feature here justifies inventing an explanation. No dedicated A→C taxonomy sample was selected; A→C outcome classification is complete, and every selected record retains C predictions.'
i=next(i for i,line in enumerate(lines) if line.startswith('These are hypotheses about visible'))
lines[i]+='\n\n'+boundary
with (A/'TAXONOMY_SUMMARY.md').open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(lines))
with (A/'TAXONOMY_COMPLETION.json').open('x',encoding='utf8') as f:
    json.dump({'at_utc':datetime.now(timezone.utc).isoformat(),'status':'COVERAGE_COMPLETE_AI_CODED_UNBLINDED','unique_claims_coded':len(annotations),'selected_cases_coded':len(rows),'codebook_sha256':freeze['codebook_sha256'],'human_review':False,'independent_coding':False,'agreement_statistic':None,'unchanged_frozen_scores':True,'annotation_files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('annotations_*.tsv')}},f,indent=2)
print(json.dumps({'selected_groups':aggregates,'full_dataset':full}))
