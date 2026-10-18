"""Failure-path tests using disposable publication fixtures; no experiment calls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile

SPEC=importlib.util.spec_from_file_location('publication_check',Path(__file__).resolve().parents[1]/'verify_publication.py')
CHECK=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CHECK)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in ['manuscript.tex','manuscript.pdf','manuscript.docx']:
            (self.root/name).write_bytes(('fixture '+name).encode())
        (self.root/'supplement').mkdir();(self.root/'supplement/record.txt').write_text('verified record',encoding='utf8')
        with zipfile.ZipFile(self.root/'supplements-S1-S5.zip','w') as archive:
            archive.write(self.root/'supplement/record.txt','supplement/record.txt')
        agreement={key:CHECK.digest(self.root/name) for name,key in [('manuscript.tex','source_sha256'),('manuscript.pdf','pdf_sha256'),('manuscript.docx','word_sha256')]}
        (self.root/'DOCUMENT_AGREEMENT.json').write_text(json.dumps(agreement),encoding='utf8')
        self.refresh_manifest()

    def refresh_manifest(self):
        rows=[{'path':p.relative_to(self.root).as_posix(),'sha256':CHECK.digest(p)} for p in self.root.rglob('*') if p.is_file() and p.name!='PUBLICATION_MANIFEST.json']
        (self.root/'PUBLICATION_MANIFEST.json').write_text(json.dumps({'files':rows}),encoding='utf8')

    def test_valid_package(self):
        self.assertEqual(CHECK.verify(self.root)['status'],'PASS')

    def test_changed_manuscript_is_rejected(self):
        (self.root/'manuscript.tex').write_text('changed',encoding='utf8')
        result=CHECK.verify(self.root)
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any('Hash mismatch: manuscript.tex' in e for e in result['errors']))

    def test_missing_document_is_rejected(self):
        (self.root/'manuscript.pdf').unlink()
        self.assertIn('Missing file: manuscript.pdf',CHECK.verify(self.root)['errors'])

    def test_manifest_traversal_is_rejected(self):
        path=self.root/'PUBLICATION_MANIFEST.json';data=json.loads(path.read_text())
        data['files'].append({'path':'../outside.txt','sha256':'unused'});path.write_text(json.dumps(data))
        self.assertTrue(any('Unsafe' in e for e in CHECK.verify(self.root)['errors']))

    def test_corrupt_archive_is_rejected_even_with_updated_manifest(self):
        (self.root/'supplements-S1-S5.zip').write_bytes(b'not a zip');self.refresh_manifest()
        self.assertTrue(any('Invalid supplement ZIP' in e for e in CHECK.verify(self.root)['errors']))

    def test_invalid_manifest_is_rejected(self):
        (self.root/'PUBLICATION_MANIFEST.json').write_text('{invalid',encoding='utf8')
        self.assertEqual(CHECK.verify(self.root)['status'],'FAIL')


if __name__=='__main__':unittest.main()
