# BazarIQ 2024 regional comparison fix

* Replaces the fragile LLM SQL planning for explicit Tashkent city vs Namangan region annual deal-count comparisons with direct read-only SQLite.
* Explicit date range: >= 2024-01-01 and < 2025-01-01.
* Uses deals.region (trade region), not participant registration region.
* Computes difference and relative percentage using Namangan as denominator.
* Russian and Uzbek output. No Gemini request required for this query.
* Does not disable SQL validation or database authorizer.

To deploy: upload analyst.py and fastpath.py into GitHub repository root, commit, then Render -> Manual Deploy -> Deploy latest commit. Both must be replaced together.

To test: python -m unittest discover -s tests -q
