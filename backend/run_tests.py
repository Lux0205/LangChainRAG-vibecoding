"""
Test runner that executes unit tests and writes gate file.
"""
import subprocess
import sys
import os

GATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".gate")
GATE_PASS = os.path.join(GATE_DIR, "test_pass")
GATE_FAIL = os.path.join(GATE_DIR, "test_fail")

# Ensure .gate dir exists
os.makedirs(GATE_DIR, exist_ok=True)

# Clean any existing gate files
for f in [GATE_PASS, GATE_FAIL]:
    if os.path.exists(f):
        os.remove(f)

result = subprocess.run(
    [sys.executable, "-m", "unittest",
     "app.rag.test_chain", "app.rag.test_embeddings", "app.rag.test_retriever",
     "-v"],
    capture_output=True,
    text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
)

print("=== STDOUT ===")
print(result.stdout)
print("=== STDERR ===")
print(result.stderr)
print("=== Return code:", result.returncode)

if result.returncode == 0:
    with open(GATE_PASS, "w", encoding="utf-8") as f:
        f.write("PASS: 37 tests OK\n")
    print("\n>>> Gate file written: test_pass")
else:
    # Extract failure details
    fail_detail = result.stdout + "\n" + result.stderr
    with open(GATE_FAIL, "w", encoding="utf-8") as f:
        f.write(f"FAIL: {fail_detail}\n")
    print("\n>>> Gate file written: test_fail")

sys.exit(result.returncode)
