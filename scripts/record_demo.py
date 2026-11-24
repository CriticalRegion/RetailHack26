"""Record the Iris demo with burned-in captions -> demo/iris-demo.webm (then scripts converts to mp4/gif).

Needs the API (:8000) and web app (:5173) running. Run: .venv/Scripts/python scripts/record_demo.py
"""
import shutil
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo"
WEB, API = "http://localhost:5173", "http://localhost:8000"

CAPTION_JS = """(t) => {
  let el = document.getElementById('demo-caption');
  if (!el) {
    el = document.createElement('div');
    el.id = 'demo-caption';
    Object.assign(el.style, {position:'fixed', left:'50%', bottom:'28px', transform:'translateX(-50%)', zIndex:99999,
      maxWidth:'1050px', padding:'14px 22px', borderRadius:'12px', background:'rgba(20,24,19,0.88)', color:'#fff',
      font:'600 22px/1.35 Inter, system-ui, sans-serif', textAlign:'center', boxShadow:'0 10px 30px rgba(0,0,0,.25)'});
    document.body.appendChild(el);
  }
  el.textContent = t;
}"""


def main() -> int:
    urllib.request.urlopen(urllib.request.Request(API + "/api/reset", method="POST"), timeout=10).read()
    tmp = OUT / "_rec"
    shutil.rmtree(tmp, ignore_errors=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(tmp),
                            record_video_size={"width": 1440, "height": 900})
        pg = ctx.new_page()
        say = lambda t, ms=3500: (pg.evaluate(CAPTION_JS, t), pg.wait_for_timeout(ms))  # noqa: E731
        show = lambda loc: (loc.scroll_into_view_if_needed(), pg.wait_for_timeout(600))  # noqa: E731

        pg.goto(WEB)
        pg.wait_for_selector("text=This week's stock")
        say("Iris: a buying assistant for a barbershop owner. It turns next week's bookings + a stock count into an order.", 5000)
        say("Right now 22 appointments can't be done: the matte clay runs out on Friday at 11:00.", 4500)
        show(pg.get_by_text("Your week", exact=False).first)
        say("The week view reads like the appointment book: Friday onwards is short.", 4500)

        show(pg.get_by_role("button", name="Use sample photo"))
        say("Step 1: count the shelf. Iris reads a stocktake photo with a Nebius-hosted vision model (Gemma 3).", 3500)
        pg.get_by_role("button", name="Use sample photo").click()
        pg.evaluate(CAPTION_JS, "Reading the photo on Nebius Token Factory…")
        pg.get_by_label("Confirm Northline Matte Clay").wait_for(timeout=90000)
        show(pg.get_by_label("Confirm Northline Matte Clay"))
        say("It read 120 ml of clay and 400 neck strips. Nothing changes stock until the owner ticks each row.", 4500)
        pg.get_by_label("Confirm Northline Matte Clay").check()
        pg.get_by_label("Confirm Barberline Neck Strips").check()
        pg.get_by_role("button", name="Confirm 2 counts").click()
        say("Counts confirmed. The forecast is recomputed in code from booking recipes.", 3500)

        run = pg.get_by_test_id("run")
        show(run)
        say("Step 2: Iris searches suppliers for the exact product and size, delivered before Friday 11:00.", 4000)
        run.click()
        pg.get_by_test_id("approve").wait_for(timeout=60000)
        show(pg.get_by_text("Iris suggests").first)
        say("Suggestion: BarberHub, £26.50, arrives Wednesday — in time. Price and delivery are checked in code.", 5000)
        show(pg.get_by_text("Other options Iris checked").first)
        say("Cheaper BulkBarber arrives Monday — too late for 16 appointments, so it's not suggested.", 5000)

        show(pg.get_by_role("button", name="Try a different supplier"))
        say("Step 3: the owner can say no, in plain words.", 3000)
        pg.get_by_role("button", name="Try a different supplier").click()
        pg.get_by_label("Reject with feedback").type("not BarberHub, they were late last time", delay=35)
        pg.wait_for_timeout(800)
        pg.get_by_test_id("reject").click()
        pg.get_by_text("You said").first.wait_for(timeout=60000)
        show(pg.get_by_text("Iris suggests").first)
        say("Iris searched again without BarberHub: ShearCo, £37.95, still in time. Nothing has been ordered.", 5500)

        pg.get_by_test_id("approve").click()
        pg.get_by_test_id("order-confirm").wait_for(timeout=30000)
        show(pg.get_by_test_id("order-confirm"))
        say("Step 4: approve → a simulated order. All 22 appointments go ahead (£602 of bookings covered).", 5500)
        pg.get_by_test_id("approve-again").click()
        pg.wait_for_timeout(1200)
        say("Approving twice still creates exactly one order — the order path is idempotent.", 4500)
        pg.mouse.wheel(0, -4000)
        pg.wait_for_timeout(800)
        say("The week now shows Thursday's delivery and Friday's appointments saved.", 4000)
        show(pg.get_by_text("Your week", exact=False).first)
        say("Iris · Nebius Token Factory (Gemma 3 vision, Nemotron text) · Tavily · NVIDIA retail blueprint patterns", 5000)

        video = pg.video.path()
        ctx.close()
        b.close()
    dst = OUT / "iris-demo.webm"
    shutil.move(video, dst)
    shutil.rmtree(tmp, ignore_errors=True)
    print("saved", dst)
    urllib.request.urlopen(urllib.request.Request(API + "/api/reset", method="POST"), timeout=10).read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
