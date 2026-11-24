| id | owner | status | deps | ref |
|---|---|---|---|---|
| t0-scaffold | @infosui | done | - | - |
| t1-schemas | @criticalregion | done | t0-scaffold | iris/data.py |
| t2-data-forecast | @criticalregion | done | t1-schemas | iris/calc.py, data/*.json |
| t3-intake | @infosui | done | t1-schemas | - |
| t4-sourcing | @criticalregion | done | t1-schemas | branch t4-sourcing (iris/sourcing.py, iris/agent.py) |
| t5-app-orders | @abhi | done | t1-schemas | - |
| t6-e2e-demo | @abhi | done | t2-data-forecast,t3-intake,t4-sourcing,t5-app-orders | - |
| t7-api | - | todo | - | files: server.py, tests/test_api.py; do: FastAPI over iris.calc/agent/orders/intake per contracts/api.md, CORS for localhost:5173, uvicorn server:app --port 8000; done: every contract endpoint returns the contract JSON, demo path via curl; owner hint: CriticalRegion |
| t8-web-shell | - | todo | - | files: web/ (scaffold, src/App.tsx, src/theme, src/components/{Stepper,KpiHero,Intake}*, src/api.ts, src/mock/); do: Vite React TS Tailwind, layout, stepper, KPI hero, stock intake screen with LIVE/REPLAY badges, api.ts with mock fallback; done: npm run dev shows the flow on mocks; owner hint: Om |
