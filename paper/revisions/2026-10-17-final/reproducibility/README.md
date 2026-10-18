# Reproducibility sources and final provenance

This addition publishes previously missing source scripts and completed verification records. It changes no manuscript, result, coding annotation or frozen experiment file. [Source manifest](SOURCE_MANIFEST.json) records original locations and byte hashes; it also lists operational scripts/tests already present in the frozen public snapshot so they are not duplicated here.

## Check the downloaded publication

Python 3.10 or later and its standard library are sufficient:

```sh
python reproducibility/verify_publication.py
python -m unittest discover -s reproducibility/tests -p "test_*.py"
```

Run these commands from the [dated manuscript directory](../README.md). The checker verifies the publication manifest, exact source/PDF/Word hashes against the completed agreement record, and supplementary ZIP members. It reads files only. The tests exercise valid packages, changed/missing files, invalid manifests, path traversal and corrupt archives. These are publication integrity tests; they do not repeat the scientific audit or make model calls.

## Reproduce the editable Word export

The unchanged [export_word.py](../export_word.py) generated the completed Word version. Work in a **separate copy** of the manuscript directory; the exporter writes manuscript.docx and reports/word-equivalence.json there.

1. Compile manuscript.tex with bibliography and figure: `tectonic -X compile --untrusted --keep-intermediates manuscript.tex`. The exporter needs the generated manuscript.aux and manuscript.bbl.
2. Install the recorded Python dependencies from [requirements-word.txt](requirements-word.txt). The original export used Python 3.12.14, python-docx 1.2.0 and lxml 6.1.1.
3. The original Windows export requires the installed Office transform at `C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL`. It is not redistributed. Create reports/ in the working copy, then run `python export_word.py`.

The published Word/PDF/source remain the inspected originals. Full native Microsoft Word pagination is not certified; the completed revision inspected all PDF pages and bounded Word content renders. This addition does not rerun the exporter, compiler or scientific analysis.

## Archived offline source snapshots

- [audit_statistics.py](source-snapshots/audit_statistics.py): independent numerical/bootstrap reconstruction used in the existing audit.
- [classify_and_select.py](source-snapshots/classify_and_select.py): complete outcome classification and seeded selected-case sampling.
- [assemble_taxonomy.py](source-snapshots/assemble_taxonomy.py) and [verify_taxonomy.py](source-snapshots/verify_taxonomy.py): original version-1 annotation assembly and lineage checks.
- [prepare_recheck.py](source-snapshots/prepare_recheck.py) and [assemble_recheck.py](source-snapshots/assemble_recheck.py): second-review selection/assembly that produced the separately versioned exploratory records.

These exact historical scripts retain their original directory assumptions and, in several cases, exclusive-output writes. **They are source snapshots, not portable commands to run in this directory.** They require their original preserved input tree and fresh output locations. They do not independently create or human-validate the interpretive annotations. Current version-2 data and review limits remain in [Supplement S3](../supplement/SUPPLEMENT.md#s3-selected-coding-assessment-results-and-review-history); version-1 scripts do not supersede them. Do not rerun them against completed outputs.

## Completed final-revision records

[provenance/](provenance/) retains the final claim/citation ledgers, result-preservation checks, Word/source equivalence, bounded Word-render record, compilation/layout checks and citation identities. Absolute and source-project-relative paths inside these reports document their original environment, not portable file links. Missing QA images, intermediate drafts and old input-tree dependencies are not being claimed as newly included. Navigate from [the supplement index](../supplement/SUPPLEMENT.md) for public supporting files.

Credentials, raw requests/responses, databases, private backups, caches, QA renders, earlier drafts and the email draft are excluded. The [frozen public snapshot](../../../../replacement_predictor_v1/published/full3-2026-10-17/README.md) already preserves operational runtime sources and tests.
