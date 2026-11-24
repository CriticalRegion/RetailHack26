"""End-to-end acceptance checks from IRIS.md, run headless against app.py.

Run: python scripts/acceptance.py   (exit 1 on any failure)
"""
from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = ""):
    results.append((name, bool(ok), detail))


def fresh() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    return at


def btn(at: AppTest, label: str):
    return next(b for b in at.button if b.label.startswith(label))


def texts(els) -> list[str]:
    return [e.value for e in els]


def n_orders(at: AppTest) -> str:
    return next(m.value for m in at.metric if m.label == "Simulated orders")


# 1. Demo path: forecast -> basket -> reject -> approve -> duplicate approve ---------------
at = fresh()
risk = [e for e in texts(at.error) if "Runs out" in e]
check("first at-risk booking shown", risk, risk[0][:80] if risk else "no run-out banner")

btn(at, "Run Iris").click().run()
r1 = texts(at.subheader)
check("r1 proposal created", any("r1 · PROPOSED" in s for s in r1), str(r1))
check("no order before approval", n_orders(at) == "0")
late = [d for d in at.dataframe if "LATE" in d.value.to_string()]
check("late cheaper offer shown with missed bookings", late)
leads = [d for d in at.dataframe if "lead:" in d.value.to_string()]
check("wrong-size / no-ETA listings kept as leads", leads)

at.text_input[0].input("not BarberHub, they were late last time").run()
btn(at, "Reject").click().run()
r2 = texts(at.subheader)
check("reject -> r2 with different supplier", any("r2 · PROPOSED" in s for s in r2), str(r2))
check("still no order after rejection", n_orders(at) == "0")
check("feedback shown on revision", any("Revised after feedback" in c for c in texts(at.caption)))

btn(at, "Approve r2").click().run()
check("approve -> one order", n_orders(at) == "1")
check("coverage updated after order", any("Covered" in s for s in texts(at.success)))
btn(at, "Approve r2 again").click().run()
check("second approval -> still one order", n_orders(at) == "1")
btn(at, "Mark received").click().run()
check("received moves pending to on-hand", any("received" in s for s in texts(at.success)))
check("no exceptions on demo path", not at.exception, str(at.exception))

# 2. No alternative after rejection ----------------------------------------------------
at = fresh()
btn(at, "Run Iris").click().run()
btn(at, "Reject").click().run()
btn(at, "Reject").click().run()
check("no on-time alternative -> unmet need shown", any("no on-time offer left" in w for w in texts(at.warning)))
check("empty basket cannot be approved", btn(at, "Approve r").disabled)

# 3. Text intake changes the forecast; unreadable count stays unknown --------------------
at = fresh()
before = [e for e in texts(at.error) if "Runs out" in e]
at.text_area[0].input("3 x Northline Matte Clay 100 ml, lots of neck strips").run()
btn(at, "Read text").click().run()
btn(at, "Confirm counts").click().run()
after = [e for e in texts(at.error) if "Runs out" in e]
check("confirmed clay count changes the forecast", before and not after, f"{len(before)} -> {len(after)} run-out banners")
check("unreadable count not applied", any("1 count(s) confirmed" in s for s in texts(at.success)),
      str(texts(at.success)))

# report -------------------------------------------------------------------------------
w = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(w)}  {detail if not ok else ''}")
failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} acceptance checks passed")
sys.exit(1 if failed else 0)
