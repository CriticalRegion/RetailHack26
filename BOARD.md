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
| t16-ui-shell-restyle | @abhi | doing | - | files: web/src/App.tsx, web/src/components/{Stepper,KpiHero,Timeline}.tsx (classNames only); do: restyle per web/STYLE.md (Flux UI look: zinc, hairline cards, Inter, small badges instead of tinted cards, quieter header, KPI values zinc-900 with status badge, Recharts colours per STYLE.md); keep testids/labels/behaviour; done: npm --prefix web run build OK + browser check, pushed by 19:15; owner hint: CriticalRegion |
| t17-ui-intake-restyle | @abhi | done | - | - |
