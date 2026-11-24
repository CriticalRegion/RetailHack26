# Decisions (one line each, never re-argue)
18:11 @infosui t3 intake stays on labelled FALLBACK/REPLAY until a human fills .env; no further open tasks except t6 (Abhi), so @infosui stops rather than duplicating t6 work
18:13 @abhi Demo runs in fixture mode by default (live search toggle off); live Nebius only if keys are in .env on the demo laptop and tested before 19:35
18:16 @abhi Security scan: all 16 FAILs are upstream NVIDIA blueprint placeholders (doc/test dummy passwords/tokens, .npmrc legacy-peer-deps, .env.example template) already public upstream - no rotation, leave blueprints unmodified. Our code (app.py, iris/, data/, scripts/) clean; .env gitignored
18:16 @infosui BuilderBase: @abhi submits (owns demo/SUBMISSION.md and presents); @infosui and @criticalregion do NOT submit
18:17 @criticalregion Om (@infosui) submits on BuilderBase, using demo/SUBMISSION.md; nobody else submits
18:18 @infosui SUPERSEDES earlier: Om (@infosui's human) submits on BuilderBase per @criticalregion's human; Abhi presents; nobody else submits
