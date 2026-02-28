"""
Run all visualization scripts in sequence.
"""

import subprocess
import sys
import os

scripts_dir = os.path.dirname(os.path.abspath(__file__))

charts = [
    ("Geographic Segment Performance", "insight_geographic_segments.py"),
    ("New Business Profit Trends", "insight_new_business_profit.py"),
    ("EEV Equity Bridge", "insight_eev_equity_bridge.py"),
    ("Capital & Solvency Position", "insight_capital_solvency.py"),
]


failed = []
for title, script in charts:
    print(f"-> {title}")
    result = subprocess.run(
        [sys.executable, script],
        cwd=scripts_dir,
    )
    if result.returncode != 0:
        print(f"   ERROR: {script} failed with return code {result.returncode}")
        failed.append(script)
    else:
        print(f"   Done.")

print()
if failed:
    print(f"Finished with errors in: {', '.join(failed)}")
else:
    print("All visualizations completed successfully.")
