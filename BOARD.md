| id | owner | status | deps | ref |
|---|---|---|---|---|
| t0-scaffold | @infosui | done | - | - |
| t1-schemas | - | todo | t0-scaffold | files: iris/data.py; do: canonical SKUs (hero: matte clay ml, neck strips), pydantic records for forecast line, supplier offer, proposal/order, fixed demo clock; done: all 4 owners import it, agreed by 18:00; owner hint: Tudor |
| t2-data-forecast | - | todo | t1-schemas | files: data/*.json, iris/calc.py; do: synthetic bookings+recipes+stocktake+3 clay offers (2 on-time, 1 cheaper late), 7-day demand, time-ordered stock projection, first at-risk booking; done: hero clay shortfall reproduced by a test, edited count changes forecast; owner hint: Tudor |
| t3-intake | @infosui | doing | t1-schemas | files: iris/llm.py, iris/intake.py; do: Nebius OpenAI-compatible client, photo->VLM and text->LLM router, extraction schema, SKU matching, review rows, labelled replay fallback; done: staged photo and pasted text both yield confirmed on-hand counts; owner hint: Om |
| t4-sourcing | @criticalregion | done | t1-schemas | branch t4-sourcing (iris/sourcing.py, iris/agent.py) |
| t5-app-orders | @abhi | done | t1-schemas | - |
| t6-e2e-demo | - | todo | t2-data-forecast,t3-intake,t4-sourcing,t5-app-orders | files: scripts/, README, demo/; do: stitch end to end, acceptance checks from IRIS.md, polish, backup recording, BuilderBase entry text; done: demo path 1-4 green by 19:35, entry ready by 19:50; owner hint: Abhi + all |
