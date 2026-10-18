"""Complete outcome classification and bounded, seeded post-result case selection."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import random

A = Path(__file__).resolve().parent
E = A.parents[1]
F = E/'reports/full3-final-2026-10-17T13-43-20.656767+00-00'
SEED = 20261017
OUTCOME_NAMES = ('stayed_correct', 'rescue', 'regression', 'stayed_wrong')


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines()]


def write_csv(name, rows):
    with (A/name).open('x', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def write_json(name, value):
    with (A/name).open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, indent=2); f.write('\n')


def outcome(a, b):
    return 'stayed_correct' if a and b else 'regression' if a else 'rescue' if b else 'stayed_wrong'


records = read(F/'OUTCOMES.jsonl')
inputs = {r['claim_id']: {**r, 'source_input_line': i} for i, r in enumerate(read(E/'prepared/inputs.jsonl'), 1)}
index = {(o['claim_id'], o['model'], o['condition'], o['repetition']): o for o in records}
models = sorted({o['model'] for o in records})
ids = sorted({o['claim_id'] for o in records})
assert len(index) == len(records) == 180000
assert len(ids) == 10000 and all(o['state'] == 'valid' for o in records)
comparisons = {}; case_rows = []; summary = []; variability = []
for model in models:
    for contrast in ('AB', 'BC', 'AC'):
        group_counts = collections.Counter(); group_claims = collections.defaultdict(set)
        patterns = collections.defaultdict(list)
        for cid in ids:
            outcomes = [outcome(index[cid, model, contrast[0], rep]['correct'], index[cid, model, contrast[1], rep]['correct']) for rep in (1, 2, 3)]
            counts = collections.Counter(outcomes)
            key = (cid, model, contrast)
            comparisons[key] = outcomes
            vector = tuple(counts[g] for g in OUTCOME_NAMES)
            patterns[vector].append(cid)
            case_rows.append({'claim_id':cid, 'model':model, 'contrast':contrast, 'r1':outcomes[0], 'r2':outcomes[1], 'r3':outcomes[2], **{g:counts[g] for g in OUTCOME_NAMES}, 'pattern':'consistent_'+outcomes[0] if len(set(outcomes)) == 1 else 'mixed', 'distinct_claim_unit':1})
            for rep, group in enumerate(outcomes, 1):
                group_counts[rep, group] += 1
                group_claims[group].add(cid)
        for rep in (1, 2, 3):
            assert sum(group_counts[rep, group] for group in OUTCOME_NAMES) == 10000
            for group in OUTCOME_NAMES:
                n = group_counts[rep, group]
                summary.append({'row_type':'by_repetition', 'model':model, 'contrast':contrast, 'repetition':rep, 'outcome':group, 'comparison_count':n, 'distinct_claim_count':n, 'assigned_comparisons':10000, 'assigned_distinct_claims':10000, 'pattern_stayed_correct':'', 'pattern_rescue':'', 'pattern_regression':'', 'pattern_stayed_wrong':''})
        for group in OUTCOME_NAMES:
            summary.append({'row_type':'all_repetitions', 'model':model, 'contrast':contrast, 'repetition':'1;2;3', 'outcome':group, 'comparison_count':sum(group_counts[rep, group] for rep in (1,2,3)), 'distinct_claim_count':len(group_claims[group]), 'assigned_comparisons':30000, 'assigned_distinct_claims':10000, 'pattern_stayed_correct':'', 'pattern_rescue':'', 'pattern_regression':'', 'pattern_stayed_wrong':''})
        for vector, cids in sorted(patterns.items()):
            summary.append({'row_type':'within_claim_pattern', 'model':model, 'contrast':contrast, 'repetition':'1;2;3', 'outcome':'consistent_'+OUTCOME_NAMES[vector.index(3)] if 3 in vector else 'mixed', 'comparison_count':3*len(cids), 'distinct_claim_count':len(cids), 'assigned_comparisons':30000, 'assigned_distinct_claims':10000, **{'pattern_'+g:n for g,n in zip(OUTCOME_NAMES, vector)}})
    for condition in 'ABC':
        for cid in ids:
            labels = [index[cid, model, condition, r]['label'] for r in (1,2,3)]
            correct = [index[cid, model, condition, r]['correct'] for r in (1,2,3)]
            disagree = sum(labels[i] != labels[j] for i,j in ((0,1),(0,2),(1,2)))
            directional = sum(correct[i] and not correct[j] for i in range(3) for j in range(3) if i != j)
            variability.append({'claim_id':cid, 'model':model, 'condition':condition, 'r1':labels[0], 'r2':labels[1], 'r3':labels[2], 'disagreeing_unordered_pairs':disagree, 'assigned_unordered_pairs':3, 'disagreement_fraction':disagree/3, 'directional_correct_to_wrong_ordered_pairs':directional, 'assigned_ordered_pairs':6, 'directional_loss_fraction':directional/6, 'any_label_variability':len(set(labels))>1})
write_csv('OUTCOME_SUMMARY.csv', summary)
write_csv('COMPARISON_CASES.csv', case_rows)
write_csv('IDENTICAL_PROMPT_VARIABILITY.csv', variability)

# Each eligible group has its own derived seed: membership is insensitive to other groups' sizes.
groups = []; selected = collections.defaultdict(list)
for model in models:
    definitions = [('AB_regression_all3','AB',lambda out:out.count('regression')==3,None), ('BC_regression_all3','BC',lambda out:out.count('regression')==3,None)]
    definitions += [('AB_firstpass_'+g,'AB',lambda out,g=g:out[0]==g,30) for g in ('rescue','stayed_wrong','stayed_correct')]
    definitions += [('AB_regression_some_not_all','AB',lambda out:0<out.count('regression')<3,20)]
    for route, contrast, predicate, cap in definitions:
        eligible = [cid for cid in ids if predicate(comparisons[cid, model, contrast])]
        seed = int.from_bytes(hashlib.sha256(f'{SEED}|{model}|{route}'.encode()).digest()[:8], 'big')
        chosen = eligible if cap is None else sorted(random.Random(seed).sample(eligible, min(cap,len(eligible))))
        name = model+'/'+route
        groups.append({'group':name,'model':model,'contrast':contrast,'eligible_model_claim_cases':len(eligible),'eligible_distinct_claims':len(eligible),'selected_model_claim_cases':len(chosen),'selected_distinct_claims':len(chosen),'cap':'all' if cap is None else cap,'master_seed':SEED,'group_seed':seed,'rule':'all eligible' if cap is None else 'random.sample without replacement from sorted claim IDs'})
        for cid in chosen:selected[cid, model, contrast].append(name)
assert sum(len([key for key in selected if key[2]=='AB' and comparisons[key].count('regression')==3]) for _ in [0]) == 186
persistent = [key for key in selected if key[2]=='AB' and comparisons[key].count('regression')==3]
assert len({key[0] for key in persistent}) == 160
group_map = {g['group']:g for g in groups}
sample = []
for (cid, model, contrast), flags in sorted(selected.items()):
    source = inputs[cid]; os = comparisons[cid,model,contrast]
    sample.append({'case_id':cid+'|'+model+'|'+contrast, 'claim_id':cid,'model':model,'contrast':contrast,'master_seed':SEED,'selection_flags':';'.join(flags),'eligible_populations':json.dumps({flag:group_map[flag]['eligible_model_claim_cases'] for flag in flags},sort_keys=True),'group_seeds':json.dumps({flag:group_map[flag]['group_seed'] for flag in flags},sort_keys=True),'r1_outcome':os[0],'r2_outcome':os[1],'r3_outcome':os[2],'regression_repetitions':os.count('regression'),'source_input_line':source['source_input_line'],'source_input':'prepared/inputs.jsonl','annotation_unit':'claim_id; reusable feature annotation across model/contrast cases'})
write_csv('SAMPLE_GROUPS.csv',groups)
write_csv('TAXONOMY_SAMPLE.csv',sample)

# Five distinct claims per broad route, spanning both models where available.
pilot=[];used=set();rng=random.Random(SEED+1)
routes=('AB_regression_all3','BC_regression_all3','AB_firstpass_rescue','AB_firstpass_stayed_wrong','AB_firstpass_stayed_correct','AB_regression_some_not_all')
for route in routes:
    candidates=[row for row in sample if any(flag.endswith('/'+route) for flag in row['selection_flags'].split(';'))]
    rng.shuffle(candidates)
    for j in range(5):
        preferred=models[j%len(models)]
        options=[row for row in candidates if row['claim_id'] not in used and row['model']==preferred]
        if not options:options=[row for row in candidates if row['claim_id'] not in used]
        row=options[0];used.add(row['claim_id']);pilot.append({**row,'pilot_route':route,'pilot_order':len(pilot)+1})
write_csv('PILOT_SAMPLE.csv',pilot)
selected_ids=sorted({r['claim_id'] for r in sample})
reader=[]
for cid in selected_ids:
    r=inputs[cid]
    reader.append({**r,'selected_cases':[x['case_id'] for x in sample if x['claim_id']==cid],'selection_flags':sorted({flag for x in sample if x['claim_id']==cid for flag in x['selection_flags'].split(';')}),'predictions':{model:{c:[index[cid,model,c,rep]['label'] for rep in (1,2,3)] for c in 'ABC'} for model in models},'pilot':cid in used})
with (A/'SELECTED_CLAIM_RECORDS.jsonl').open('x',encoding='utf8',newline='\n') as f:
    for row in reader:f.write(json.dumps(row,ensure_ascii=False)+'\n')
clusters=collections.defaultdict(list)
for cid in ids:clusters[inputs[cid]['text_cluster']].append(cid)
diagnostics={'claims':len(ids),'text_clusters':len(clusters),'clusters_with_multiple_records':sum(len(v)>1 for v in clusters.values()),'claims_in_duplicate_text_clusters':sum(len(v) for v in clusters.values() if len(v)>1),'clusters_with_conflicting_gold_labels':sum(len({inputs[cid]['gold_label'] for cid in v})>1 for v in clusters.values()),'gold_counts':dict(collections.Counter(inputs[cid]['gold_label'] for cid in ids)),'models':models,'complete_case_rows':len(case_rows),'summary_rows':len(summary),'sample_cases':len(sample),'sample_distinct_claims':len(selected_ids),'ab_all3_model_claim_cases':len(persistent),'ab_all3_distinct_claims':len({k[0] for k in persistent}),'bc_all3_model_claim_cases':sum(r['contrast']=='BC' for r in sample),'pilot_unique_claims':len(pilot),'selection_not_population_prevalence':True}
write_json('SELECTION_AND_COVERAGE.json',diagnostics)
write_json('SELECTION_FREEZE.json',{'master_seed':SEED,'seed_derivation':'first 8 SHA256 bytes, big-endian integer, of master_seed|model|route','python_rng':'Python random.Random / sample; no replacement within group','sample_files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (A/'TAXONOMY_SAMPLE.csv',A/'PILOT_SAMPLE.csv',A/'SELECTED_CLAIM_RECORDS.jsonl',A/'SAMPLE_GROUPS.csv')},'case_deduplication':'claim_id, model, contrast; all selection flags retained','feature_annotation_reuse':'claim_id across models and contrasts','pilot_rule':'five unique claims per six broad routes, alternating model preference; master_seed+1 shuffles; no coding before this file'})
print(json.dumps(diagnostics))
