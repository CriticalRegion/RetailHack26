| id | owner | status | deps | ref |
|---|---|---|---|---|
| t0-scaffold | @infosui | done | - | - |
| t1-schemas | @criticalregion | done | t0-scaffold | iris/data.py |
| t2-data-forecast | @criticalregion | done | t1-schemas | iris/calc.py, data/*.json |
| t3-intake | @infosui | done | t1-schemas | - |
| t4-sourcing | @criticalregion | done | t1-schemas | branch t4-sourcing (iris/sourcing.py, iris/agent.py) |
| t5-app-orders | @abhi | done | t1-schemas | - |
| t6-e2e-demo | @abhi | doing | t2-data-forecast,t3-intake,t4-sourcing,t5-app-orders | files: scripts/, README, demo/; do: stitch end to end, acceptance checks from IRIS.md, polish, backup recording, BuilderBase entry text; done: demo path 1-4 green by 19:35, entry ready by 19:50; owner hint: Abhi + all |
