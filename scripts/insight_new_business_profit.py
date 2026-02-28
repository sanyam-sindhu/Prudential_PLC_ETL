
## New Business Profitability & Growth Trends

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("../output_csv/02_new_business_profit.csv")
aer = df[df.Basis == 'AER'].copy()

def get_metric(metric, unit):
    filtered = aer[(aer.Metric == metric) & (aer.Unit == unit)]
    return filtered.set_index('Fiscal_Year')['Value']

years = [2020, 2021, 2022]
nbp = get_metric('New business profit', '$m')
margin = get_metric('New business margin (APE)', '%')

nbp_vals = [nbp.get(y, float('nan')) for y in years]
margin_vals = [margin.get(y, float('nan')) for y in years]

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_title("New Business Profit vs Margin (2020-2022, AER)",
             fontsize=14, fontweight='bold', pad=12)

x = np.arange(len(years))

bars = ax.bar(x, nbp_vals, 0.5, color='blue', label='NBP (USD m)')
ax.bar_label(bars, labels=['$' + f'{int(v):,}m' for v in nbp_vals], padding=5)

ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], fontsize=11)
ax.set_ylabel('New Business Profit (USD m)')
ax.set_ylim(0, max(nbp_vals) * 1.25)
ax.grid(axis='y', alpha=0.3)

ax_right = ax.twinx()
ax_right.plot(x, margin_vals, 'o-', color='red', linewidth=2.5,
              markersize=8, label='NBP Margin (%)')
for xi, v in zip(x, margin_vals):
    ax_right.annotate(f'{int(v)}%', (xi, v), textcoords="offset points",
                      xytext=(0, 10), ha='center', color='red')

ax_right.set_ylabel('NBP Margin (%)', color='red')
ax_right.set_ylim(40, 70)
ax_right.tick_params(axis='y', labelcolor='red')




lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_right.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ape = get_metric('Annual premium equivalent (APE)', '$m')
eev_op = get_metric('EEV operating profit', '$m')
nbp_chg = (nbp[2022] - nbp[2021]) / nbp[2021] * 100
ape_chg = (ape[2022] - ape[2021]) / ape[2021] * 100
eev_chg = (eev_op[2022] - eev_op[2021]) / eev_op[2021] * 100

insight_text = (
    f"Insights:\n"
    f"1. NBP fell {abs(nbp_chg):.0f}% ({int(nbp[2021])}m to {int(nbp[2022])}m) "
    f"despite APE growing {ape_chg:.0f}% to {int(ape[2022])}m - volume up, value down\n"
    f"2. NBP margin compressed from {int(margin[2021])}% to {int(margin[2022])}%, "
    f"signaling a shift toward lower-margin products or pricing pressure\n"
    f"3. EEV operating profit rose {eev_chg:.0f}% to {int(eev_op[2022])}m, "
    f"showing strong in-force book earnings offsetting weaker new business"
)
fig.text(0.5, -0.06, insight_text, ha='center', va='top', fontsize=9, wrap=True)

plt.tight_layout()
plt.savefig("../output_csv/charts/insight_02_new_business_profit.png", bbox_inches='tight')
print("Saved: ../output_csv/charts/insight_02_new_business_profit.png")
