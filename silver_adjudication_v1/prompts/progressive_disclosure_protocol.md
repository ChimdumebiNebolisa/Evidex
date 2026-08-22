# Progressive Disclosure Protocol (silver adjudication, v1)

Each claim is adjudicated through three strictly sequential stages. A judge's
earlier-stage answer is frozen before the next stage's extra evidence is
revealed, and later information never rewrites a stored earlier answer.

## Stage A — sentence-only evidence (matches the original experiment prompt)

Judge sees:
- `claim`
- `evidence_sentences`: the resolved gold evidence sentences, concatenated
  (exactly the `gold_evidence` text the GPT models saw)

Nothing else.

## Stage B — add page titles

Judge sees:
- `claim`
- `evidence_sentences` (same as A)
- `page_titles`: the FEVER evidence page titles for the evidence sentences,
  in source order, one per evidence sentence (e.g. `[page, sentence i]`)

The judge may change its verdict; changes from Stage A are recorded.

## Stage C — structured FEVER evidence

Judge sees:
- `claim`
- full structure recovered from the immutable FEVER evidence annotation:
  - page titles
  - evidence-set boundaries
  - per-sentence source page and line index
  - the selected (shortest complete) evidence set with sentence texts in
    annotation order
  - alternative complete evidence sets from the same annotation, with their
    sentence texts where recoverable from the official FEVER wiki archive
    (downloaded read-only; see METHODS)

Nothing beyond the FEVER source annotation is added. No web browsing, no
external retrieval.

## Freezing

- All judges complete Stage A for all items → Stage A outputs hashed and
  frozen → Stage B built and run → frozen → Stage C → frozen.
- Judgments are append-only; a stage's file never changes after its freeze
  hash is recorded.
- Consensus, resolver, and silver labels are computed only after all three
  stages are frozen, and are themselves frozen before any unblinding join.
