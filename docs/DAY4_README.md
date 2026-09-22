# Day 4 — Few-Shot Retrieval with FAISS

## What this adds

Day 3's chain was zero-shot: schema + business rules only, no examples.
Day 4 adds retrieval-augmented few-shot prompting:

1. `data/few_shot_examples.jsonl` — 31 curated, validated question→SQL
   pairs covering the schema's common query patterns (single-table
   filters, joins across `project_assignments`, group-bys, an explicit
   refusal example)
2. `query_engine/build_faiss_index.py` — embeds each question with a
   local `sentence-transformers` model (`all-MiniLM-L6-v2`, free, no API
   calls) and builds a FAISS index
3. `query_engine/retriever.py` — at query time, embeds the user's
   question and retrieves the top-5 most similar examples from the index
4. `query_engine/nl2sql_chain.py` — injects those retrieved examples into
   the system prompt before generation, and supports toggling few-shot
   on/off (`toggle` command) so you can compare both modes live

## Setup

```bash
# one-time: build the index from the curated examples
python query_engine/build_faiss_index.py
```

This downloads the embedding model (~90MB) from Hugging Face on first
run and caches it locally — after that it's fully offline, no ongoing
API cost. Produces `data_pipeline/faiss_store/index.faiss` and
`examples.json`.

## Run it

```bash
python query_engine/nl2sql_chain.py
```

```
> how many civil engineers work in Moscow
[few-shot examples retrieved and injected into the prompt automatically]
Generated SQL:
  SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer' AND city = 'Moscow';
```

Type `toggle` to switch to zero-shot mode and compare — this is how you
generate your own before/after numbers for Day 6's evaluation.

## What I verified without a live LLM call

This sandbox can't reach Hugging Face's servers to download the real
embedding model, so I verified the actual `build_faiss_index.py` and
`retriever.py` code by temporarily substituting a TF-IDF vectorizer in
place of `sentence-transformers` — same FAISS mechanics, different
embedding source. Confirmed:
- The index builds correctly from `few_shot_examples.jsonl` (31 vectors)
- Retrieval correctly ranks semantically relevant examples first — e.g.
  a query about "engineers in Istanbul" correctly retrieved the
  data-analyst-in-Istanbul and civil-engineer-in-Moscow examples ahead of
  unrelated ones
- The prompt-formatting function produces valid Q/SQL blocks

Run `python query_engine/build_faiss_index.py` yourself with a normal
internet connection — Hugging Face Hub access works fine outside this
sandbox, and the same code path applies.

## Expected impact (measure this yourself in Day 6)

The reference paper reports 0-shot → 5-shot query validity improving
from 76.4% to 91.8% (+15.4 points). Your numbers will differ since your
schema and question set are smaller and simpler, but you should see a
real, measurable improvement, especially on multi-table join questions
— those are exactly the cases Day 3's zero-shot baseline struggled with.

## Next: Day 5

Add the validation and safety layer: schema whitelist checking (reject
SQL referencing tables/columns that don't exist), and a hard block on
any query touching sensitive columns — building on top of the basic
`is_safe_select` guard from Day 3.
