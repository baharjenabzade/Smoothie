# Reference answers (RAG)

Add your graded answers as `.json` / `.jsonl` files in `knowledge/samples/` (copy `_template.json`;
files starting with `_` are ignored). Required: `part` (1-3), `question`, `answer`, `band`.
Optional: `topic`, `fluency`, `lexical`, `grammar` (bands), `notes` (why it got that band).

For each evaluation the app retrieves up to 3 samples of the same part, preferring similar
questions/topics and different bands, and shows them to the AI as calibration. Restart the server
after changing files. Check them with `python -m app.rag_check`.

Tips: 15-30 samples per part across bands 4-8 works far better than many at one band. Notes
that name the evidence ("no complex sentences", "wrong collocation: make a research") help most.
