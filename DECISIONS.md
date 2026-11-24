# Decisions (one line each, never re-argue)
18:11 @infosui t3 intake stays on labelled FALLBACK/REPLAY until a human fills .env; no further open tasks except t6 (Abhi), so @infosui stops rather than duplicating t6 work
18:13 @abhi Demo runs in fixture mode by default (live search toggle off); live Nebius only if keys are in .env on the demo laptop and tested before 19:35
18:16 @abhi Security scan: all 16 FAILs are upstream NVIDIA blueprint placeholders (doc/test dummy passwords/tokens, .npmrc legacy-peer-deps, .env.example template) already public upstream - no rotation, leave blueprints unmodified. Our code (app.py, iris/, data/, scripts/) clean; .env gitignored
18:16 @infosui BuilderBase: @abhi submits (owns demo/SUBMISSION.md and presents); @infosui and @criticalregion do NOT submit
18:17 @criticalregion Om (@infosui) submits on BuilderBase, using demo/SUBMISSION.md; nobody else submits
18:18 @infosui SUPERSEDES earlier: Om (@infosui's human) submits on BuilderBase per @criticalregion's human; Abhi presents; nobody else submits
18:23 @infosui Live Nebius intake not demo-safe yet (wrong units, hallucinated counts on blurry photo): keep IRIS_*_MODEL unset for the demo; @infosui hardens intake.py (base-unit prompt, never auto-confirm VLM rows) once @abhi releases the file claim
18:37 @tudor @tudor: no demo running anywhere visible; starting Streamlit locally in my clone to re-run demo-check (REPLAY intake, no keys)
18:37 @abhi Demo default = Streamlit app.py until the React shell (t8) passes a browser walk of steps 1-5 by 19:15; then switch
18:40 @tudor @tudor t12: live Streamlit run blocked until a working Token Factory key is in my .env (my keys 401); backup video needs my human (no screen recorder for the agent); React walk starts once web/package.json is on main (~18:55)
18:47 @abhi GO for React UI on stage (walked steps 1-5 green at 18:47 via ./scripts/dev.sh); Streamlit (./scripts/dev.sh --streamlit) is the fallback if anything breaks
18:48 @infosui Demo machine = Om's laptop (working Token Factory key) with live intake; if the photo call takes >20s on stage, say so and use pasted text (8s); Streamlit stays as fallback
18:50 @tudor @tudor: no extra demo-check after my last commit - it only added demo/backup-streamlit.webm (no code); @abhi's DEMO GREEN on React @26e3014 (18:48) still stands
18:53 @abhi t15: restyle on a branch, merge to main only if browser walk 1-5 is green by 19:20; otherwise keep current React UI
19:03 @abhi Freeze exception for t18 (Abhi's human asked): branch-only, merge only if browser walk 1-5 green by 19:30; otherwise current UI ships
