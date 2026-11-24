# Plan (event section by /hackathon:setup, plan by /hackathon:kickoff)
## Event
- Name / dates: Retail AI & Agents Hackathon | Innovators Guild, hosted at Fresha (Old St, London), 2026-11-24
- Deadline (local): code freeze 20:00 Europe/London today. Demos 20:20-20:45; sign up with the facilitator before 20:20
- Brief / theme: Tracks: (1) Retail AI, Nebius/NVIDIA: agentic commerce, product discovery, shopping workflows, catalog enrichment. (2) Agentic AI, Nebius Token Factory: "one user, one problem, one workflow". (3) Partner track TBC. Own project allowed. Host: Fresha (salon/barber booking platform)
- Sponsor or required tech: Nebius Token Factory, NVIDIA, Tavily. Credits not confirmed, so keep our own keys as a fallback. Public, synthetic or authorised data only
- Judging criteria (weights): not a formal competition, no prizes. Optional 3-min demo: who it's for and the problem, what we built, what works and what we learned, what's next
- Submission requirements (video, repo, live URL, pitch length): 3-min live demo plus a backup recording or screenshots. No video, repo or URL rule
- Team (handle: skills, usage-window start): @abhi: CS, Python/JS, window started ~17:00. Teammates: unknown
- Links (Devpost, Discord, docs): https://luma.com/1ri4tr1c ; https://builderbase.com/event/innovators-guild-hackathon
## Plan
- One-line pitch: Iris, "Never run out of what's booked": turns next week's appointments and a stock count (photo or text) into a justified supplier basket the owner approves, rejects with feedback, or orders (simulated). Barbershop demo, generic schema. Full spec: IRIS.md (Idea A in IDEAS.md)
- Submission: BuilderBase (https://builderbase.com/event/innovators-guild-hackathon), team deadline 20:00 London time (24 Nov 2026). Demo slot sign-up with the facilitator before 20:20
- Demo path (3-5 steps a judge will see):
  1. Upload staged stock photo, confirm detected clay count (text intake shown briefly), change a count and watch the forecast move
  2. Run Iris: first at-risk appointment and responsible services, supplier offers with price/delivery evidence, why the cheaper seller misses Friday
  3. Reject the proposed supplier with feedback: revised basket, still no order
  4. Approve the revised basket: one simulated order, new incoming stock, updated coverage; retry approval = still one order
  5. (If time) tattoo preset or "Why so much clay?"
- Stack: Python + Streamlit, small modules (iris/*), Nebius Token Factory via OpenAI-compatible client (Nemotron text, image-capable VLM), Tavily search, JSON synthetic data. Runs locally
- Scaffold command (official starter/generator): none (single `app.py` + `iris/` package per IRIS.md); `pip install streamlit openai tavily-python python-dotenv pydantic`
- Mocked, not integrated (FAKE:): supplier offers (labelled fixture, 2 on-time + 1 cheaper late for the hero SKU), live extraction replay if endpoint fails, orders and payments (simulated local order only), Fresha bookings (synthetic), supplier emails
- Owners (directory -> @name): data/ + iris/calc.py + iris/data.py -> Tudor (tizzy1); iris/llm.py + iris/intake.py -> Om (@infosui, Infosuii); iris/sourcing.py + iris/agent.py -> CriticalRegion; app.py + iris/orders.py + demo/BuilderBase materials -> Abhi (@abhi, abhit-7). Confirm in team chat
- Dev command / local URL: `streamlit run app.py` / http://localhost:8501
- Live URL: none (local demo)
- Milestones (clock time, London): [ ] 18:00 schemas agreed, clay shortage + 2 offers seeded, Nebius text/image + Tavily + blueprint seam smoke-tested  [ ] 18:45 end-to-end: stock -> forecast -> basket -> reject -> simulated order  [ ] 19:15 real photo/text extraction + one live supplier lookup, fixture run ready  [ ] 19:35 acceptance checks, polish, backup recording  [ ] 19:50 BuilderBase entry prepared, submit before 20:00
## Cut list (not building)
Ask Iris chat, extra presets (tattoo only if time), supplier emails, history/trend polish, 14-day view. Out of scope: real Fresha integration, live ordering, real payments, accounts, mobile, deploying the full NVIDIA blueprint stacks
