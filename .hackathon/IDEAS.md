# Ideas (from /hackathon:kickoff; /hackathon:pivot reads the runners-up)

Status: 4 candidates, NO decision yet. Do not pick one or start building until the team chooses.

Likely stack for any of them: Python + Streamlit, Nebius Token Factory via the OpenAI SDK, Tavily, JSON synthetic data.

## IDEA A: Stock manager for salons/barbers (working name Backbar; needs a new name)
Reads the next 14 days of Fresha bookings + notes, predicts which products run out, and gives the owner a justified shopping list to approve. Insight: salons know demand in advance, and each service has a product recipe. Code does the maths (recipe x bookings - stock = shortfall and run-out date). AI interprets notes ("very long hair" = 1.5x colour), spots trends ("textured crops +60%"), picks suppliers (price/rating/arrives in time) and writes one-line reasons. Owner approves, then mock orders + drafted supplier emails. Stretch: "Ask me" chat, Tavily supplier search, cost per service, shrinkage alert. Screens: run-out timeline, shopping list with Approve/Edit/Remove, confirmation with £ saved and services protected.

## IDEA B: Agent-to-agent booking
The shopper's agent ("skin fade, under £25, near Old St, before Friday") negotiates with 4-5 simulated salon agents that fill empty slots with discounts; it compares, haggles once, then books (mock). Split view: chat + live negotiation log + salon calendar filling. Most wow, most risk (multi-agent loops, may overlap Fresha AI Concierge).

## IDEA C: Empty-chair pricing
Finds slots predicted to stay empty in the next 7 days, picks the clients most likely to book, writes personal offers, the owner approves, offers sent (mock), tracks results. Heatmap empty to filled, "+£340 this week". Risk: weak retail link, similar to existing tools.

## IDEA D: Photo consult
The client uploads their current hair + an inspiration photo; vision describes the gap; the agent maps it to services, time and price range, books the right slot length, flags a patch test, and writes a stylist brief. Risk: vision accuracy, and photo/personal-data rules.
