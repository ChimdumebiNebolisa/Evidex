"""Version exploratory coding and expose every second-review decision."""
import collections
import csv
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path

O=Path(__file__).resolve().parent
S=O.parent/'evidex-full3-source-20261017'
Q=O/'taxonomy-review'

def rows(path,delimiter=','):
    with path.open(encoding='utf8',newline='') as f:return list(csv.DictReader(f,delimiter=delimiter))

def write_csv(name,rs):
    with (Q/name).open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)

original=rows(S/'audit/TAXONOMY_CASES.csv')
byclaim=collections.defaultdict(list)
for r in original:byclaim[r['claim_id']].append(r)
full=list(map(json.loads,(Q/'RECHECK_PACKETS.jsonl').read_text(encoding='utf8').splitlines()))
target=list(map(json.loads,(Q/'TARGETED_PACKETS.jsonl').read_text(encoding='utf8').splitlines()))
packets={r['claim_id']:r for r in full+target}
decisions={};history=[]
for name in ['conflict_decisions.tsv','nonconflict_decisions.tsv']+[p.name for p in sorted(Q.glob('targeted_*.tsv'))]+['followup_corrections.tsv']:
    for r in rows(Q/name,'\t'):
        cid=r['claim_id'];old=byclaim[cid][0];prior=decisions.get(cid)
        assessment=old['evidence_reference_assessment'] if r['revised_assessment']=='UNCHANGED' else r['revised_assessment']
        categories=old['categories'] if r['revised_categories']=='UNCHANGED' else r['revised_categories']
        assert assessment in ('supports_gold','conflicts_gold','insufficient','ambiguous')
        assert set(categories.split(';')) <= {'NEG','SCOPE','REL','ENT','NUM','LEX','CTX','GAP','TXT','DIRECT','UNCLEAR'}
        assert 'DIRECT' not in categories.split(';') or categories=='DIRECT'
        decision={**r,'revised_assessment':assessment,'revised_categories':categories,'decision_source':name}
        decisions[cid]=decision
        history.append({'claim_id':cid,'source':name,'prior_decision':prior,'decision':decision})
assert set(decisions)==set(packets) and len(decisions)==230
original_conflicts={r['claim_id'] for r in full if r['review_route']=='all_original_conflicts'}
assert len(original_conflicts)==43
assert {r['claim_id'] for r in rows(Q/'nonconflict_decisions.tsv','\t')}=={r['claim_id'] for r in full if r['review_route']=='seeded_nonconflict'}
assert {r['claim_id'] for r in target}=={r['claim_id'] for p in Q.glob('targeted_*.tsv') for r in rows(p,'\t')}
version_hash=hashlib.sha256((Q/'REGRESSION_CODEBOOK_v2.md').read_bytes()).hexdigest()
assert version_hash==json.loads((Q/'TARGETED_SELECTION.json').read_text())['v2_codebook_sha256']
annotation_rows=[];change_rows=[];revised=[]
for cid,rs in sorted(byclaim.items()):
    old=rs[0];d=decisions.get(cid)
    annotation_rows.append({'claim_id':cid,'original_assessment':old['evidence_reference_assessment'],
        'revised_assessment':d['revised_assessment'] if d else old['evidence_reference_assessment'],
        'original_categories':old['categories'],'revised_categories':d['revised_categories'] if d else old['categories'],
        'second_review_scope':'full' if cid in {x['claim_id'] for x in full} else 'targeted_NUM_NEG_TXT_rule_check' if d else 'not_second_reviewed',
        'changed':bool(d and (d['revised_assessment']!=old['evidence_reference_assessment'] or d['revised_categories']!=old['categories'])),
        'justification':d['justification'] if d else 'Original annotation retained; no second review of this claim.',
        'human_review':'PENDING','independent_coder':False})
    if annotation_rows[-1]['changed']:change_rows.append(annotation_rows[-1])
    for r in rs:
        row=dict(r)
        row.update(original_categories=r['categories'],original_evidence_reference_assessment=r['evidence_reference_assessment'],
            original_justification=r['justification'],second_review_scope=annotation_rows[-1]['second_review_scope'],
            coding_version='2',coding_codebook_sha256=version_hash,human_review='PENDING')
        if d:
            row.update(categories=d['revised_categories'],evidence_reference_assessment=d['revised_assessment'],justification=d['justification'])
        row['review_status']='AI-coded_unblinded; second_AI_review_'+('performed' if d else 'not_performed')+'; human_review_pending'
        row['uncertainty']='Exploratory supplied-text assessment; literal, contextual and identity assumptions remain stated. No benchmark score or internal-reasoning conclusion changes.'
        row['human_review_priority']='high' if row['evidence_reference_assessment']!='supports_gold' else 'routine'
        revised.append(row)
write_csv('ANNOTATION_REVIEW_COVERAGE.csv',annotation_rows)
write_csv('CODING_CHANGE_LOG.csv',change_rows)
write_csv('TAXONOMY_CASES_v2.csv',revised)
ann={str(r['id']):r for r in map(json.loads,(S/'reference/shared_task_dev.jsonl').read_text(encoding='utf8').splitlines())}
conflict_rows=[]
for cid in sorted(original_conflicts):
    p=packets[cid];d=decisions[cid];rs=byclaim[cid];ref=ann[cid]
    assert p['claim']==ref['claim'] and p['reference'].upper()==ref['label'].replace('SUPPORTS','SUPPORTED').replace('REFUTES','REFUTED')
    conflict_rows.append({'claim_id':cid,'models':';'.join(sorted({r['model'] for r in rs})),
        'selected_case_ids':';'.join(r['case_id'] for r in rs),'claim':p['claim'],'complete_selected_evidence':p['selected_evidence'],
        'frozen_reference':p['reference'],'FEVER_original_label':ref['label'],
        'FEVER_original_evidence_annotations':json.dumps(ref['evidence'],ensure_ascii=False),
        'predictions_all_models_conditions_repetitions':json.dumps(p['predictions'],ensure_ascii=False),
        'original_flag':p['original_assessment'],'original_justification':p['original_justification'],
        'recheck_classification':d['flag_status'],'revised_assessment':d['revised_assessment'],
        'revised_categories':d['revised_categories'],'recheck_justification':d['justification'],
        'reviewer':'AI; same assistant; unblinded','human_review':'PENDING','benchmark_labels_and_scores_changed':False})
write_csv('REFERENCE_CONFLICT_REVIEW.csv',conflict_rows)
body=['<!doctype html><meta charset="utf-8"><title>Evidex reference flag review</title><style>body{font:16px/1.5 Georgia,serif;max-width:1100px;margin:36px auto;padding:0 24px;color:#17212b}article{border-top:1px solid #bbb;margin-top:28px;padding-top:16px}table{border-collapse:collapse;width:100%;font:14px/1.4 Arial,sans-serif}th,td{border:1px solid #ccc;padding:8px;text-align:left}th{background:#eef2f5}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1,h2{line-height:1.2}.flag{font-family:Arial,sans-serif;color:#384b60}</style><h1>Evidex review of 43 original reference conflict flags</h1><p>Second AI review, unblinded, by the same assistant. Human review is pending for every record. Original FEVER labels and benchmark scores remain unchanged. Complete selected evidence and both models’ repeated predictions appear below; S means Supported and R means Refuted. Original annotation pointers provide provenance, not extra text supplied to the predictors.</p>']
esc=lambda x:html.escape(str(x))
for r in conflict_rows:
    body.append(f'<article id="claim-{r["claim_id"]}"><h2>Claim {r["claim_id"]}</h2><p><strong>{esc(r["claim"])}</strong></p><p>{esc(r["complete_selected_evidence"])}</p><p class="flag">Frozen reference: {esc(r["frozen_reference"])} · Original FEVER: {esc(r["FEVER_original_label"])} · Recheck: {esc(r["recheck_classification"])} → {esc(r["revised_assessment"])}</p><table><tr><th>Model</th><th>A repetitions 1, 2, 3</th><th>B repetitions 1, 2, 3</th><th>C repetitions 1, 2, 3</th></tr>')
    for m,cs in json.loads(r['predictions_all_models_conditions_repetitions']).items():
        body.append('<tr><td>'+esc(m)+'</td>'+''.join('<td>'+','.join(x[0] for x in cs[c])+'</td>' for c in 'ABC')+'</tr>')
    body.append(f'</table><p><b>Original flag:</b> {esc(r["original_justification"])}</p><p><b>Second-review assessment:</b> {esc(r["recheck_justification"])}</p><details><summary>Original FEVER annotation pointers and selected cases</summary><pre>{esc(r["FEVER_original_evidence_annotations"])}\n{esc(r["selected_case_ids"])}</pre></details><p><b>Human judgment:</b> pending</p></article>')
(Q/'REFERENCE_CONFLICT_REVIEW.html').write_text('\n'.join(body),encoding='utf8')
category_rows=[]
routes=sorted({flag.split('/',1)[1] for r in revised for flag in r['selection_flags'].split(';')})
for route in routes:
    group=[r for r in revised if any(f.endswith('/'+route) for f in r['selection_flags'].split(';'))]
    for code in sorted({x for r in revised for x in r['categories'].split(';')}):
        subset=[r for r in group if code in r['categories'].split(';')]
        category_rows.append({'selection_route':route,'category':code,'case_count':len(subset),
            'case_denominator':len(group),'distinct_claim_count':len({r['claim_id'] for r in subset}),
            'distinct_claim_denominator':len({r['claim_id'] for r in group})})
write_csv('CATEGORY_COUNTS_v2.csv',category_rows)
counts=collections.Counter(r['revised_assessment'] for r in annotation_rows)
summary={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'SECOND_AI_REVIEW_COMPLETE_WITH_LIMITS',
    'original_conflict_claims':43,'original_conflict_recheck_classifications':dict(collections.Counter(r['recheck_classification'] for r in conflict_rows)),
    'full_second_review_claims':99,'seeded_nonconflict_claims':56,'targeted_additional_claims':131,
    'total_second_review_claims':230,'not_second_reviewed_claims':186,'total_selected_claims':416,
    'total_selected_cases':len(revised),'second_reviewed_cases':sum(r['second_review_scope']!='not_second_reviewed' for r in revised),
    'changed_claim_annotations':len(change_rows),'assessment_changed_claims':sum(r['original_assessment']!=r['revised_assessment'] for r in change_rows),
    'feature_changed_claims':sum(r['original_categories']!=r['revised_categories'] for r in change_rows),
    'v2_distinct_claim_alignment_counts':dict(counts),'v2_codebook_sha256':version_hash,
    'scope':'Same-assistant unblinded AI recheck; no human validation or independent-coder agreement; selected counts are not population prevalence',
    'benchmark_scoring':'UNCHANGED'}
(Q/'RECHECK_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
(Q/'DECISION_HISTORY.json').write_text(json.dumps(history,indent=2),encoding='utf8')
dest=S/'review-v2';dest.mkdir(exist_ok=True)
for name in ('TAXONOMY_CASES_v2.csv','CATEGORY_COUNTS_v2.csv','RECHECK_SUMMARY.json','CODING_CHANGE_LOG.csv','REFERENCE_CONFLICT_REVIEW.csv','ANNOTATION_REVIEW_COVERAGE.csv','REGRESSION_CODEBOOK_v2.md'):
    (dest/name).write_bytes((Q/name).read_bytes())
print(json.dumps(summary))
