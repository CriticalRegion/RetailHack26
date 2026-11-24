| id | owner | status | deps | ref |
|---|---|---|---|---|
| t0-scaffold | @infosui | done | - | - |
| t1-schemas | @criticalregion | done | t0-scaffold | iris/data.py |
| t2-data-forecast | @criticalregion | done | t1-schemas | iris/calc.py, data/*.json |
| t3-intake | @infosui | done | t1-schemas | - |
| t4-sourcing | @criticalregion | done | t1-schemas | branch t4-sourcing (iris/sourcing.py, iris/agent.py) |
| t5-app-orders | @abhi | done | t1-schemas | - |
| t6-e2e-demo | @abhi | done | t2-data-forecast,t3-intake,t4-sourcing,t5-app-orders | - |
| t7-api | @infosui | done | - | - |
| t8-web-shell | @infosui | doing | - | files: web/ (scaffold, src/App.tsx, src/theme, src/components/{Stepper,KpiHero,Intake}*, src/api.ts, src/mock/); do: Vite React TS Tailwind, layout, stepper, KPI hero, stock intake screen with LIVE/REPLAY badges, api.ts with mock fallback; done: npm run dev shows the flow on mocks; owner hint: Om |
| t9-web-basket | @abhi | done | t8-web-shell | - |
| t10-web-timeline | @criticalregion | doing | t8-web-shell | files: web/src/components/Timeline*, demo/; do: Recharts run-out chart (stock vs bookings, red first-at-risk marker, dashed after-order line), screenshots, update demo/SCRIPT.md + SUBMISSION.md for the React UI; done: chart on mocks, screenshots refreshed; owner hint: Tudor or whoever is free |
| t11-run-and-docs | - | todo | - | files: README.md, scripts/dev.sh, scripts/dev.ps1, demo/SUBMISSION.md; do: one-command start of API (uvicorn server:app :8000) + web (npm --prefix web run dev :5173) for mac and windows, README 'Run the React UI' section, BuilderBase entry final text (React UI + Nebius models nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B text, google/gemma-3-27b-it vision, NVIDIA blueprint patterns, live vs simulated table); done: fresh clone starts both with one command; owner hint: Abhi |
