| id | owner | status | deps | ref |
|---|---|---|---|---|
| t0-scaffold | - | todo | - | files: requirements.txt, app.py (stub), iris/__init__.py, scripts/smoke.py; do: pip deps, empty module stubs per IRIS.md, smoke script for Nebius text+image and Tavily, streamlit hello runs; done: streamlit run app.py shows stub, smoke prints OK/FAIL per service; owner hint: Om |
| t1-schemas | - | todo | t0-scaffold | files: iris/data.py; do: canonical SKUs (hero: matte clay ml, neck strips), pydantic records for forecast line, supplier offer, proposal/order, fixed demo clock; done: all 4 owners import it, agreed by 18:00; owner hint: Tudor |
| t2-data-forecast | - | todo | t1-schemas | files: data/*.json, iris/calc.py; do: synthetic bookings+recipes+stocktake+3 clay offers (2 on-time, 1 cheaper late), 7-day demand, time-ordered stock projection, first at-risk booking; done: hero clay shortfall reproduced by a test, edited count changes forecast; owner hint: Tudor |
