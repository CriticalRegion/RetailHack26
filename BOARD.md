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
| t12-live-qa | @tudor | doing | - | files: demo/ (recording, notes only); do: with a filled .env (NEBIUS_API_KEY, TAVILY_API_KEY, IRIS_TEXT_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B, IRIS_VISION_MODEL=google/gemma-3-27b-it) run the Streamlit fallback live: sample photo, pasted text, live search toggle; record a 2-3 min backup video of the full demo path; from ~18:55 walk the React UI (web/ + server.py) steps 1-5 in a browser and post every gap as hk note @infosui; done: backup video in demo/, gap list posted; owner hint: Tudor |
| t13-streamlit-polish | @tudor | done | - | app.py:164 |
| t14-live-verify | @infosui | done | - | - |
