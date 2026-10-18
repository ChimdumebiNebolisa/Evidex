"""Freeze a bounded second-AI-review sample and complete review packets."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import random

O=Path(__file__).resolve().parent
S=O.parent/'evidex-full3-source-20261017'
A=S/'audit'
Q=O/'taxonomy-review'
Q.mkdir(exist_ok=True)

def rows(path):
    with path.open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))

cases=rows(A/'TAXONOMY_CASES.csv')
byclaim=collections.defaultdict(list)
for r in cases:byclaim[r['claim_id']].append(r)
inputs={r['claim_id']:r for r in map(json.loads,(S/'experiment/prepared/inputs.jsonl').read_text(encoding='utf8').splitlines())}
annotations={str(r['id']):r for r in map(json.loads,(S/'reference/shared_task_dev.jsonl').read_text(encoding='utf8').splitlines())}
conflicts=sorted(cid for cid,rs in byclaim.items() if rs[0]['evidence_reference_assessment']=='conflicts_gold')
assert len(conflicts)==43
seed=20261018
selected=collections.defaultdict(list);group_rows=[]
routes=sorted({flag.split('/',1)[1] for r in cases for flag in r['selection_flags'].split(';')})
for group in routes+sorted({code for r in cases for code in r['categories'].split(';')}):
    candidates=sorted(cid for cid,rs in byclaim.items() if cid not in conflicts and
        (any(any(f.endswith('/'+group) for f in r['selection_flags'].split(';')) for r in rs) if group in routes else group in rs[0]['categories'].split(';')))
    n=min(6 if group in routes else 2,len(candidates))
    derived=int.from_bytes(hashlib.sha256(f'{seed}|{group}'.encode()).digest()[:8],'big')
    chosen=sorted(random.Random(derived).sample(candidates,n))
    for cid in chosen:selected[cid].append(group)
    group_rows.append({'group':group,'eligible_distinct_claims':len(candidates),'selected_count':n,'derived_seed':derived,'claim_ids':chosen})

packets=[]
for cid in sorted(set(conflicts)|set(selected)):
    rs=byclaim[cid];x=inputs[cid];ann=annotations[cid]
    assert x['claim_text']==ann['claim'] and x['gold_label'].upper()==ann['label'].replace('SUPPORTS','SUPPORTED').replace('REFUTES','REFUTED')
    packet={'claim_id':cid,'review_route':'all_original_conflicts' if cid in conflicts else 'seeded_nonconflict',
        'sampling_flags':selected.get(cid,[]),'claim':x['claim_text'],'selected_evidence':x['gold_evidence'],
        'reference':x['gold_label'],'original_assessment':rs[0]['evidence_reference_assessment'],
        'original_features':rs[0]['categories'],'original_justification':rs[0]['justification'],
        'fever_annotation':ann,'frozen_input':x,
        'case_ids':[r['case_id'] for r in rs],
        'predictions':{m:{c:[next(r for r in rs if r['model']==m)[f'{c}_r{k}'] for k in (1,2,3)] for c in 'ABC'} for m in {r['model'] for r in rs}}}
    # Include both models, even when only one model's case was selected.
    selected_records={r['claim_id']:r for r in map(json.loads,(A/'SELECTED_CLAIM_RECORDS.jsonl').read_text(encoding='utf8').splitlines())}
    packet['predictions']=selected_records[cid]['predictions']
    packets.append(packet)
with (Q/'RECHECK_PACKETS.jsonl').open('x',encoding='utf8') as f:
    for packet in packets:f.write(json.dumps(packet,ensure_ascii=False)+'\n')
with (Q/'RECHECK_SELECTION.json').open('x',encoding='utf8') as f:
    json.dump({'master_seed':seed,'unit':'distinct claim ID; review applies to all selected model/contrast cases for that claim',
        'selection':'6 without replacement per outcome route plus 2 per feature category, sampled independently; deduplicate and retain flags',
        'groups':group_rows,'original_conflicts':conflicts,'nonconflict_ids':sorted(selected),
        'conflict_claims':43,'nonconflict_claims':len(selected),'unique_claims':len(packets),
        'reviewed_model_claim_contrast_cases':sum(len(byclaim[p['claim_id']]) for p in packets),
        'status':'SELECTION_FROZEN_BEFORE_SECOND_REVIEW','human_review':'PENDING'},f,indent=2)
print(json.dumps({'conflicts':43,'nonconflicts':len(selected),'total_claims':len(packets),'groups':group_rows}))
