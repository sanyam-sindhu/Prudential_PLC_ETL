
### Geographic Segment Performance Analysis

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("../output_csv/01_segment_results.csv")

segments = ['CPL', 'Hong Kong', 'Indonesia', 'Malaysia', 'Singapore',
            'Growth markets and other', 'Eastspring']
years = [2020, 2021, 2022]
colors = ['lightblue', 'blue', 'darkblue']

seg = df[(df['Line_Item'].isin(segments)) & (df['Basis'] == 'AER')].copy()

def get_profit(segment, year):
    row = seg[(seg['Line_Item'] == segment) & (seg['Fiscal_Year'] == year)]
    return row['Value_$m'].values[0]

fig, ax = plt.subplots(figsize=(14, 7))
ax.set_title("Geographic Segment Profit (2020-2022, AER basis)",
             fontsize=14, fontweight='bold', pad=12)

x = np.arange(len(segments))
for i, year in enumerate(years):
    vals = [get_profit(s, year) for s in segments]
    bars = ax.bar(x + i * 0.25, vals, 0.25, label=str(year), color=colors[i])
    ax.bar_label(bars, labels=[f'{int(v)}' for v in vals], padding=3, fontsize=7)

ax.set_xticks(x + 0.25)
ax.set_xticklabels([s.replace(' and other', '\n& other') for s in segments])
ax.set_ylabel('Segment Profit ($m)')
ax.legend()
ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, seg['Value_$m'].max() * 1.15)

indo_20, indo_22 = get_profit('Indonesia', 2020), get_profit('Indonesia', 2022)
indo_chg = (indo_22 - indo_20) / indo_20 * 100
hk_22 = get_profit('Hong Kong', 2022)
gm_22 = get_profit('Growth markets and other', 2022)
total_22 = sum(get_profit(s, 2022) for s in segments)
hk_share = hk_22 / total_22 * 100
gm_share = gm_22 / total_22 * 100

insight_text = (
    f"Key Findings:\n"
    f"1. Growth Markets ({int(gm_22)}m, {gm_share:.0f}%) overtook Hong Kong "
    f"({int(hk_22)}m, {hk_share:.0f}%) as the largest segment in 2022\n"
    f"2. Indonesia declined {indo_chg:.0f}% ({int(indo_20)}m to {int(indo_22)}m) "
    f"- the only segment with sustained contraction\n"
    f"3. CPL showed strongest growth momentum (+47%), "
    f"while total segment profit reached {int(total_22)}m"
)
fig.text(0.5, -0.06, insight_text, ha='center', va='top', fontsize=9, wrap=True)

plt.tight_layout()
plt.savefig("../output_csv/charts/insight_01_geographic_segments.png", bbox_inches='tight')
