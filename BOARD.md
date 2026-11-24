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
| t8-web-shell | @criticalregion | done | - | web/src/App.tsx |
| t9-web-basket | @abhi | done | t8-web-shell | - |
| t10-web-timeline | @criticalregion | done | t8-web-shell | web/src/components/Timeline.tsx, demo/screens/react-* |
| t11-run-and-docs | @abhi | done | - | - |
| t12-live-qa | @tudor | done | - | demo/backup-streamlit.webm |
| t13-streamlit-polish | @tudor | done | - | app.py:164 |
| t14-live-verify | @infosui | done | - | - |
| t15-ui-restyle | @abhi | done | - | - |
| t16-ui-shell-restyle | @abhi | done | - | - |
| t17-ui-intake-restyle | @abhi | done | - | - |
| t18-ui-dribbble | @infosui | doing | - | files: web/src/** classNames/layout only, on branch ui-dribbble (NOT main); do: make the React UI look like https://dribbble.com/shots/26985959-Health-Monitoring-Dashboard-UI-Design (open it in a browser - bots get blocked): dashboard feel, soft card grid, big KPI numbers, polished charts; keep every data-testid/label/prop/API call/behaviour; done: npm --prefix web run build OK + browser walk of demo steps 1-5 green on the branch by 19:30, then merge to main and post DEMO GREEN; not green by 19:30 = drop it, current main UI stays; owner hint: Om |
| t19-final-qa | - | todo | - | files: none (verification); do: 19:30-19:40 on the demo laptop + main: pull, browser-walk React steps 1-5 (./scripts/dev.sh), run scripts/acceptance.py, check Streamlit fallback starts (./scripts/dev.sh --streamlit); if t18 merged and anything breaks -> git checkout ui-pre-restyle or previous main for web/ and post DEMO RED/GREEN; refresh 2-3 screenshots in demo/screens if UI changed; done: DEMO GREEN posted at 19:40 with commit; owner hint: CriticalRegion |
| t20-judge-qa | - | todo | - | files: demo/QA.md; do: 8-10 likely judge questions with 1-2 line answers (what's live vs simulated, why not let the LLM pick suppliers, how it handles wrong/blurry counts, how it plugs into Fresha, data privacy, cost per run, what NVIDIA blueprint patterns, what's next), facts from README/IRIS.md/demo/SUBMISSION.md; also ask your human to record a 2-min backup video of the React UI (demo/backup-react.webm) if a screen recorder is available; done: demo/QA.md pushed by 19:35; owner hint: Tudor |
| t21-pitch | @abhi | done | - | - |
