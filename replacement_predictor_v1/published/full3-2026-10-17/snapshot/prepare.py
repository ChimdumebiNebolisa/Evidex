"""Verify and reuse historical inputs; prepare prospectively selected jobs and costs."""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import unicodedata
from pathlib import Path
from common import HERE, ROOT, MODELS, SETTINGS, RATES, SEED, encoded, digest, value_hash, write_new, request

DESIGNS = ('full1', 'full3', 'full5', 'hybrid3', 'hybrid5', 'hybrid3-historical', 'smoke')

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def ensure_file(path, value, binary=False):
    data = value if binary else encoded(value)
    if Path(path).exists():
        if Path(path).read_bytes() != data:
            raise ValueError('Refusing to replace prepared artifact: ' + str(path))
    else:
        write_new(path, data, binary=True)

def canonical(title):
    return unicodedata.normalize('NFC', title.strip())

def prepare_inputs():
    paths = {name: ROOT/name for name in ['fever_balanced_10000_v1_source.csv',
             'experiment_tracker_with_evidence_balanced_10000_v1.csv',
             'experiment_results_balanced_10000_v1.csv']}
    expected = json.loads(Path(r'C:/Users/Chimdumebi/evidex-stage2-audits/2026-10-16-6f57f49337/initial-snapshot.json').read_text(encoding='utf-8'))
    for name, p in paths.items():
        if digest(p) != expected['files'][name]['sha256']:
            raise ValueError('Historical input differs from audited record: ' + name)
    source = read_csv(paths['fever_balanced_10000_v1_source.csv'])
    tracker = read_csv(paths['experiment_tracker_with_evidence_balanced_10000_v1.csv'])
    old = read_csv(paths['experiment_results_balanced_10000_v1.csv'])
    assert len(source) == len(tracker) == 10000 and len(old) == 40000
    source = {r['claim_id']: r for r in source}
    assert len(source) == 10000 and len({r['claim_id'] for r in tracker}) == 10000
    observed = {}
    for r in old:
        k = (r['claim_id'], r['model'], r['condition'])
        assert k not in observed and r['model_output'] in ('Supported', 'Refuted')
        observed[k] = r
    needed = set()
    selected = {}
    for tr in tracker:
        cid = tr['claim_id']; src = source[cid]
        assert tr['claim_text'] == src['claim_text'] and tr['true_label'] == src['true_label']
        assert json.loads(tr['raw_evidence']) == json.loads(src['raw_evidence'])
        sentences = json.loads(tr['evidence_sentences_json'])
        assert ' '.join(sentences).strip() == tr['gold_evidence'] and tr['gold_evidence']
        matches = []
        for index, evidence_set in enumerate(json.loads(src['raw_evidence'])):
            pointers = [{'page': canonical(p[2]), 'sent_idx': int(p[3])} for p in evidence_set]
            payload = json.dumps({'set_index': index, 'pointers': pointers}, ensure_ascii=False, separators=(',', ':'))
            sid = 'fever_set_' + hashlib.sha1(payload.encode()).hexdigest()[:12]
            if sid == tr['evidence_set_id']:
                matches.append(pointers)
        assert len(matches) == 1
        ptrs = matches[0]
        assert [p['page'] for p in ptrs] == [canonical(p) for p in json.loads(tr['evidence_pages_json'])]
        assert len(ptrs) == len(sentences)
        selected[cid] = list(zip(ptrs, sentences))
        needed.update(p['page'] for p in ptrs)
        for m in MODELS:
            for c in ('claim_only', 'claim_plus_evidence'):
                r = observed[cid, m, c]
                assert all(r[k] == tr[k] for k in ('claim_text', 'true_label', 'gold_evidence', 'evidence_set_id'))
    # Direct selected-pointer verification only; no sampling or Stage C reconstruction.
    pages = {}; archives = []
    for path in sorted((ROOT/'wiki-pages/wiki-pages').glob('wiki-*.jsonl')):
        if needed <= pages.keys():
            break
        archives.append(str(path.relative_to(ROOT)))
        with path.open(encoding='utf-8') as f:
            for line in f:
                o = json.loads(line); title = canonical(o.get('id', ''))
                if title in needed:
                    text = o.get('lines', '')
                    if title in pages and pages[title] != text:
                        raise ValueError('Conflicting archive page: ' + title)
                    pages[title] = text
    if not needed <= pages.keys():
        raise ValueError('Missing archival pages; no imputation or filtering permitted')
    checked = 0
    for pairs in selected.values():
        for ptr, sentence in pairs:
            fields = [l.rstrip('\r').split('\t') for l in pages[ptr['page']].split('\n')]
            actual = [f[1] for f in fields if len(f) >= 2 and f[0] == str(ptr['sent_idx'])]
            assert actual == [sentence], ptr
            checked += 1
    result = []
    for tr in sorted(tracker, key=lambda r: int(r['claim_id'])):
        cid = tr['claim_id']; hist = {m: {c: observed[cid, m, c]['model_output'] for c in ('claim_only', 'claim_plus_evidence')} for m in MODELS}
        reg = any(v['claim_only'] == tr['true_label'] and v['claim_plus_evidence'] != tr['true_label'] for v in hist.values())
        result.append({'claim_id': cid, 'claim_text': tr['claim_text'], 'gold_label': tr['true_label'],
                       'gold_evidence': tr['gold_evidence'], 'evidence_set_id': tr['evidence_set_id'],
                       'selected_pointers': [p for p, _ in selected[cid]],
                       'text_cluster': hashlib.sha256(' '.join(tr['claim_text'].casefold().split()).encode()).hexdigest(),
                       'historical_labels': hist, 'historical_regression': reg})
    rng = random.Random(SEED)
    subset = set()
    for gold in ('Supported', 'Refuted'):
        subset.update(r['claim_id'] for r in rng.sample([r for r in result if r['gold_label'] == gold], 1000))
    for r in result:
        r['repeat_representative'] = r['claim_id'] in subset
    info = {'source_sha256': {name: digest(p) for name, p in paths.items()}, 'claims': len(result),
            'selected_sentence_pointers_checked': checked, 'archive_shards_read': archives,
            'archive_verification': 'Exact second tab field at recorded pointers, NFC titles only; no alternative evidence',
            'repeat_subset_n': len(subset), 'repeat_subset_seed': SEED,
            'repeat_subset_text_clusters': len({r['text_cluster'] for r in result if r['repeat_representative']}),
            'duplicate_clusters_full': len({r['text_cluster'] for r in result}),
            'historical_regressions': sum(r['historical_regression'] for r in result)}
    ensure_file(HERE/'prepared/inputs.jsonl', b''.join(encoded(r) for r in result), binary=True)
    ensure_file(HERE/'prepared/input-verification.json', info)
    return result

def make_jobs(claims, design):
    if design not in DESIGNS:
        raise ValueError(design)
    jobs = []
    if design == 'smoke':
        claims = [next(r for r in claims if r['gold_label'] == gold) for gold in ('Supported', 'Refuted')]
    for r in claims:
        n = int(design[-1]) if design.startswith('full') else 1
        if design.startswith('hybrid') and (r['repeat_representative'] or (design.endswith('historical') and r['historical_regression'])):
            n = 5 if design == 'hybrid5' else 3
        for model in MODELS:
            for condition in 'ABC':
                for repetition in range(1, n + 1):
                    jid = f"{r['claim_id']}_{model}_{condition}_r{repetition:02d}"
                    jobs.append({'job_id': jid, 'claim_id': r['claim_id'], 'model': model,
                                 'condition': condition, 'repetition': repetition,
                                 'request_sha256': value_hash(request(r, model, condition))})
    random.Random(SEED).shuffle(jobs)
    for order, j in enumerate(jobs):
        j['order'] = order
    return jobs

def prepare_plan(claims, design):
    jobs = make_jobs(claims, design)
    base = HERE/'prepared'/design
    ensure_file(base/'jobs.jsonl', b''.join(encoded(j) for j in jobs), binary=True)
    ensure_file(base/'plan.json', {'design': design, 'purpose': 'validation_only' if design == 'smoke' else 'new_predictor_experiment',
                'jobs': len(jobs), 'seed': SEED, 'inputs_sha256': digest(HERE/'prepared/inputs.jsonl'),
                'jobs_sha256': digest(base/'jobs.jsonl'), 'models': MODELS, 'settings': SETTINGS})
    return jobs

def price(claims):
    sys.path.insert(0, str(HERE/'.deps'))
    os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(HERE/'.deps/token-cache'))
    import tiktoken
    enc = tiktoken.get_encoding('o200k_base')
    content = {(r['claim_id'], c): len(enc.encode(request(r, MODELS[0], c)['messages'][0]['content'], disallowed_special=())) for r in claims for c in 'ABC'}
    output = max(len(enc.encode(x)) for x in ('Supported', 'Refuted'))
    estimates = []
    for design in DESIGNS:
        jobs = make_jobs(claims, design); by_model = {}
        for m in MODELS:
            js = [j for j in jobs if j['model'] == m]
            # One user role and assistant priming: a stated estimate, not provider token attestation.
            tokens = sum(content[j['claim_id'], j['condition']] + 7 for j in js)
            dollars = (tokens*RATES[m]['input'] + len(js)*output*RATES[m]['output'])/1e6
            cap = (tokens*RATES[m]['input'] + len(js)*SETTINGS['max_completion_tokens']*RATES[m]['output'])/1e6
            by_model[m] = {'calls': len(js), 'input_tokens_estimate': tokens, 'assumed_output_tokens_per_call': output,
                           'expected_usd': dollars, 'all_outputs_at_cap_usd': cap}
        estimates.append({'design': design, 'calls': len(jobs), 'models': by_model,
                          'expected_usd': sum(v['expected_usd'] for v in by_model.values()),
                          'expected_with_10_percent_extra_attempts_usd': 1.1*sum(v['expected_usd'] for v in by_model.values()),
                          'output_cap_with_10_percent_extra_attempts_usd': 1.1*sum(v['all_outputs_at_cap_usd'] for v in by_model.values()),
                          'three_attempt_policy_envelope_usd': 3*sum(v['all_outputs_at_cap_usd'] for v in by_model.values())})
    result = {'checked_date': '2026-10-16', 'tokenizer': 'tiktoken==0.12.0, o200k_base',
              'content_token_totals_one_model': {c: sum(content[r['claim_id'], c] for r in claims) for c in 'ABC'},
              'framing_allowance_tokens_per_request': 7, 'rates_per_million_usd': RATES,
              'pricing_route': 'OpenAI global standard Chat Completions; no cached-input or Batch discount assumed',
              'source': 'https://developers.openai.com/api/docs/pricing',
              'caveat': 'Content tokens counted locally; seven framing tokens estimated. Output scenario is stand-alone labels. Reasoning tokens, if any, share the 32-token completion cap and output rate. Ten percent retry scenario is not an expected failure forecast. Three-attempt envelope is conditional on token estimate, current rates and no extra runs; not a guaranteed bill. Taxes excluded.',
              'designs': estimates}
    ensure_file(HERE/'COST_ESTIMATE.json', result)
    return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--design', choices=DESIGNS, action='append'); args = parser.parse_args()
    if (HERE/'protocol-freeze.json').exists():
        raise SystemExit('Already frozen; create a separately named protocol revision to change preparation')
    claims = prepare_inputs()
    for d in args.design or ['full3', 'smoke']:
        prepare_plan(claims, d)
    estimates = price(claims)
    print(json.dumps({'inputs': len(claims), 'plans': args.design or ['full3', 'smoke'],
                      'costs': [{k: v for k, v in x.items() if k in ('design', 'calls', 'expected_usd')} for x in estimates['designs']]}, indent=2))

if __name__ == '__main__':
    main()
