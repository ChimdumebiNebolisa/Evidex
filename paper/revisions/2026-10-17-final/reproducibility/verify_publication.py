"""Read-only, offline checks for the published manuscript package (standard library)."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    root=Path(root).resolve();errors=[];checked=0
    try:
        manifest=json.loads((root/'PUBLICATION_MANIFEST.json').read_text(encoding='utf8'))
        rows=manifest['files']
        if not isinstance(rows,list):raise ValueError('files must be a list')
    except (OSError,ValueError,KeyError) as exc:
        return {'status':'FAIL','files_checked':0,'errors':['Invalid publication manifest: '+str(exc)]}
    paths=set()
    for row in rows:
        rel=row.get('path','');path=(root/rel).resolve()
        if not rel or not path.is_relative_to(root) or rel in paths:
            errors.append('Unsafe or duplicate manifest path: '+rel);continue
        paths.add(rel)
        if not path.is_file():errors.append('Missing file: '+rel);continue
        checked+=1
        if digest(path)!=row.get('sha256'):errors.append('Hash mismatch: '+rel)
    try:
        agreement=json.loads((root/'DOCUMENT_AGREEMENT.json').read_text(encoding='utf8'))
        for name,key in [('manuscript.tex','source_sha256'),('manuscript.pdf','pdf_sha256'),('manuscript.docx','word_sha256')]:
            if not (root/name).is_file() or digest(root/name)!=agreement[key]:
                errors.append('Completed manuscript agreement mismatch: '+name)
    except (OSError,ValueError,KeyError) as exc:
        errors.append('Invalid document agreement: '+str(exc))
    try:
        with zipfile.ZipFile(root/'supplements-S1-S5.zip') as archive:
            if archive.testzip() is not None:errors.append('Supplement ZIP integrity failure')
            names=archive.namelist()
            if len(names)!=len(set(names)):errors.append('Duplicate supplement ZIP members')
            for name in names:
                path=(root/name).resolve()
                if not path.is_relative_to(root/'supplement') or not path.is_file():
                    errors.append('Invalid or missing supplement ZIP member: '+name)
                elif hashlib.sha256(archive.read(name)).hexdigest()!=digest(path):
                    errors.append('Supplement ZIP member mismatch: '+name)
    except (OSError,ValueError,zipfile.BadZipFile) as exc:
        errors.append('Invalid supplement ZIP: '+str(exc))
    return {'status':'FAIL' if errors else 'PASS','files_checked':checked,'errors':errors,
            'scope':'File/ZIP integrity and completed document hashes only; no inference, scientific analysis or writes.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    result=verify(parser.parse_args().root)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)
