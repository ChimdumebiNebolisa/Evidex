"""Fixed experiment definitions. No model calls or project analysis imports."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODELS = ('gpt-5.4', 'gpt-5.4-mini')
RETURNED_MODELS = {'gpt-5.4': ['gpt-5.4', 'gpt-5.4-2026-03-05'],
                   'gpt-5.4-mini': ['gpt-5.4-mini', 'gpt-5.4-mini-2026-03-17']}
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
SETTINGS = {'temperature': 0, 'reasoning_effort': 'none', 'max_completion_tokens': 32,
            'n': 1, 'stream': False, 'store': False, 'service_tier': 'default'}
SEED = 20261016
LABELS = ('Supported', 'Refuted')
RATES = {'gpt-5.4': {'input': 2.50, 'output': 15.00},
         'gpt-5.4-mini': {'input': .75, 'output': 4.50}}

def now():
    return datetime.now(timezone.utc).isoformat()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()

def write_new(path, value, binary=False):
    """Exclusive, durable creation. A partial file is retained for explicit recovery."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(value if binary else encoded(value))
        f.flush()
        os.fsync(f.fileno())

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def messages(claim, condition):
    instruction = 'Classify the claim as Supported or Refuted'
    if condition == 'C':
        instruction += ' based only on the evidence provided'
    elif condition not in ('A', 'B'):
        raise ValueError('Unknown condition')
    content = instruction + '.\nOutput only one word: Supported or Refuted.\n\nClaim: ' + claim['claim_text']
    if condition in ('B', 'C'):
        content += '\nEvidence: ' + claim['gold_evidence']
    return [{'role': 'user', 'content': content}]

def request(claim, model, condition):
    if model not in MODELS:
        raise ValueError('Model substitution is forbidden')
    return {'model': model, 'messages': messages(claim, condition), **SETTINGS}

def read_inputs(path=None):
    return [json.loads(x) for x in Path(path or HERE/'prepared/inputs.jsonl').read_text(encoding='utf-8').splitlines() if x]

def verify_freeze(base=HERE):
    seal = load(base/'protocol-freeze.json')
    revision_path = base/'operational-revisions/2026-10-16-workers20/revision.json'
    revision = load(revision_path) if revision_path.exists() else None
    throughput_path = base/'operational-revisions/2026-10-16-rpm600/revision.json'
    throughput = load(throughput_path) if throughput_path.exists() else None
    if throughput and (not revision or digest(revision_path) != throughput['previous_revision_sha256']):
        raise ValueError('Previous operational seal changed')
    if revision and digest(base/'protocol-freeze.json') != revision['original_freeze_sha256']:
        raise ValueError('Original protocol seal changed')
    for rel, expected in seal['files'].items():
        original = revision['original_files'].get(rel, rel) if revision else rel
        if digest(base/original) != expected:
            raise ValueError('Frozen experiment file changed: ' + rel)
    if revision:
        for rel, expected in revision['files'].items():
            previous = throughput['previous_files'].get(rel,rel) if throughput else rel
            if digest(base/previous) != expected:
                raise ValueError('Operational revision file changed: ' + rel)
        seal = {**seal, 'files': {**seal['files'], **revision['files']},
                'operational_revision_sha256': digest(revision_path)}
    if throughput:
        if digest(base/'protocol-freeze.json') != throughput['original_freeze_sha256']:
            raise ValueError('Original protocol seal changed')
        for rel, expected in throughput['files'].items():
            if digest(base/rel) != expected:
                raise ValueError('Throughput revision file changed: '+rel)
        seal = {**seal,'files':{**seal['files'],**throughput['files']},
                'throughput_revision_sha256':digest(throughput_path)}
    return seal
