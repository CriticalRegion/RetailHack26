"""Fast check: compile our Python (not blueprints/) and run pytest if tests exist. Run: python scripts/check.py"""
import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ok = all(compileall.compile_dir(ROOT / d, quiet=1) for d in ("iris", "scripts") if (ROOT / d).exists())
for f in ROOT.glob("*.py"):
    ok = compileall.compile_file(f, quiet=1) and ok
if (ROOT / "tests").exists():
    ok = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")]) == 0 and ok
print("CHECK", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
