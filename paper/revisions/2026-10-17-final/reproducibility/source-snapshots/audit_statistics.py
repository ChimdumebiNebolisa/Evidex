"""Independent numerical reconstruction; writes only additional audit outputs."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

A = Path(__file__).resolve().parent
E = A.parents[1]
sys.path.insert(0, str(E/'.deps'))
import numpy as np

F = E/'reports/full3-final-2026-10-17T13-43-20.656767+00-00'
v = json.loads((F/'ANALYSIS_VERIFICATION.json').read_text())
s = json.loads((Path(v['analysis_output'])/'summary.json').read_text())
claims = [json.loads(x) for x in (E/'prepared/inputs.jsonl').read_text(encoding='utf8').splitlines()]
outcomes = [json.loads(x) for x in (F/'OUTCOMES.jsonl').read_text().splitlines()]
idx = {(o['claim_id'],o['model'],o['condition'],o['repetition']):o for o in outcomes}
models = ('gpt-5.4','gpt-5.4-mini')
metrics = {}; repeat_features = {}
for model in models:
    correct = {c: np.array([[idx[r['claim_id'],model,c,k]['label']==r['gold_label'] for k in (1,2,3)] for r in claims],dtype=float) for c in 'ABC'}
    for section, reps in [('first_pass',[0]),('repeat_representative',[0,1,2])]:
        for c in 'ABC':metrics[section,model+'/'+c+'/accuracy_ITT'] = correct[c][:,reps].mean(1)
        for pair in ('AB','BC','AC'):
            left,right = correct[pair[0]][:,reps],correct[pair[1]][:,reps]
            metrics[section,model+'/'+pair+'/known_regression_fraction'] = (left*(1-right)).mean(1)
            metrics[section,model+'/'+pair+'/known_rescue_fraction'] = ((1-left)*right).mean(1)
            metrics[section,model+'/'+pair+'/accuracy_difference_ITT'] = (right-left).mean(1)
    for c in 'ABC':
        x = correct[c]
        disagree = ((x[:,0]!=x[:,1]).astype(float)+(x[:,0]!=x[:,2])+(x[:,1]!=x[:,2]))/3
        # Binary, complete labels: correctness disagreement equals label disagreement.
        metrics['repeat_variation',model+'/'+c+'/identical_prompt_disagreement'] = disagree
        repeat_features[model+'/'+c+'/directional_loss'] = sum(x[:,i]*(1-x[:,j]) for i in range(3) for j in range(3) if i!=j)/6
    for pair in ('AB','BC'):
        metrics['repeat_variation',model+'/'+pair+'/excess_loss_over_identical_left_prompt'] = (correct[pair[0]]*(1-correct[pair[1]])).mean(1)-repeat_features[model+'/'+pair[0]+'/directional_loss']


def bootstrap(rows, values):
    clusters = sorted({r['text_cluster'] for r in rows})
    cluster_index = {c:i for i,c in enumerate(clusters)}
    n=len(clusters); m=values.shape[1]
    sums=np.zeros((2,n,m)); denominators=np.zeros((2,n))
    for r,value in zip(rows,values):
        label=0 if r['gold_label']=='Supported' else 1
        k=cluster_index[r['text_cluster']]
        sums[label,k]+=value;denominators[label,k]+=1
    proportions=denominators.sum(axis=1)/len(rows)
    rng=np.random.default_rng(20261016); draws=[]
    for start in range(0,2000,100):
        weights=rng.multinomial(n,np.full(n,1/n),size=min(100,2000-start))
        result=sum(proportions[l]*(weights@sums[l])/(weights@denominators[l])[:,None] for l in (0,1) if denominators[l].sum())
        draws.append(result)
    return np.quantile(np.concatenate(draws),[.025,.975],axis=0).T


keys=list(metrics);matrix=np.stack([metrics[k] for k in keys],axis=1)
cis=bootstrap(claims,matrix)
rows=[]
for i,(section,key) in enumerate(keys):
    frozen=s[section]['estimates'][key]
    point=frozen.get('estimate',frozen.get('estimate_complete_claims'))
    assert abs(matrix[:,i].mean()-point)<1e-12,(section,key)
    assert np.allclose(cis[i],frozen['cluster_bootstrap_95'],atol=1e-12,rtol=0),(section,key,cis[i],frozen['cluster_bootstrap_95'])
    rows.append({'section':section,'metric':key,'claims':len(claims),'clusters':9855,'independent_estimate':matrix[:,i].mean(),'independent_low':cis[i,0],'independent_high':cis[i,1],'frozen_low':frozen['cluster_bootstrap_95'][0],'frozen_high':frozen['cluster_bootstrap_95'][1],'status':'MATCH'})
mask=np.array([r['historical_regression'] for r in claims])
historical=[r for r in claims if r['historical_regression']]
hist_keys=[k for k in keys if k[0] in ('first_pass','repeat_variation')]
hist_matrix=np.stack([metrics[k][mask] for k in hist_keys],axis=1)
hist_cis=bootstrap(historical,hist_matrix)
for i,(section,key) in enumerate(hist_keys):
    dest='historical_cases_first_pass' if section=='first_pass' else 'historical_cases_repeated'
    frozen=s[dest]['estimates'][key]
    point=frozen.get('estimate',frozen.get('estimate_complete_claims'))
    assert abs(hist_matrix[:,i].mean()-point)<1e-12
    assert np.allclose(hist_cis[i],frozen['cluster_bootstrap_95'],atol=1e-12,rtol=0)
    rows.append({'section':dest,'metric':key,'claims':len(historical),'clusters':len({r['text_cluster'] for r in historical}),'independent_estimate':hist_matrix[:,i].mean(),'independent_low':hist_cis[i,0],'independent_high':hist_cis[i,1],'frozen_low':frozen['cluster_bootstrap_95'][0],'frozen_high':frozen['cluster_bootstrap_95'][1],'status':'MATCH'})
with (A/'BOOTSTRAP_REPRODUCED.csv').open('x',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Duplicate text/label diagnostics, with record identity preserved.
clusters=collections.defaultdict(list)
for r in claims:
    assert hashlib.sha256(' '.join(r['claim_text'].casefold().split()).encode()).hexdigest()==r['text_cluster']
    clusters[r['text_cluster']].append(r)
conflicts=[{'cluster':k,'records':[{'claim_id':r['claim_id'],'claim_text':r['claim_text'],'gold_label':r['gold_label'],'gold_evidence':r['gold_evidence']} for r in rs]} for k,rs in clusters.items() if len({r['gold_label'] for r in rs})>1]
result={'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),'independent_metrics_and_intervals_matched':len(rows),'bootstrap_draws':2000,'bootstrap_seed':20261016,'independent_implementation':str(Path(__file__)),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'numpy_version':np.__version__,'claims':len(claims),'text_clusters':len(clusters),'label_counts':dict(collections.Counter(r['gold_label'] for r in claims)),'historical_selected_claims':len(historical),'conflicting_reference_text_clusters':conflicts,'limits':['Descriptive percentile intervals, not simultaneous tests or equivalence tests','Fixed claim/evidence set and provider occasion; cluster resampling reflects case-composition uncertainty','Repetition 1 is primary; repeated summary includes repetition 1','Binary complete labels permit correctness-based disagreement reconstruction']}
with (A/'STATISTICAL_AUDIT.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='conflicting_reference_text_clusters'}))
