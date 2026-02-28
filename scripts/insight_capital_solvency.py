## Capital & Solvency Posn

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../output_csv/05_gws_capital_position_solvency.csv")
df_pct = df[df.Unit == '%'].copy()

def get_coverage(metric, category):
    return df_pct[(df_pct.Metric == metric) &(df_pct.Category == category)].set_index('Fiscal_Year')['Value']

cov_gmcr = get_coverage('GWS coverage ratio (over GMCR)', 'Shareholder')
cov_gpcr = get_coverage('GWS coverage ratio over GPCR', 'Shareholder')
cov_gpcr_total = get_coverage('GWS coverage ratio over GPCR', 'Total')

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_title("GWS Coverage Ratios (2020-2022)", fontsize=14, pad=12)

all_values = []
for vals, style, label, color in [
    (cov_gmcr, 'o-', 'Shareholder (GMCR)', 'blue'),
    (cov_gpcr, 's--', 'Shareholder (GPCR)', 'darkblue'),
    (cov_gpcr_total, '^:', 'Total (GPCR)', 'red'),
]:
    all_values.extend(vals.values)
    ax.plot(vals.index, vals.values, style, color=color,
            linewidth=2, markersize=8, label=label)
    for yr, v in vals.items():
        ax.annotate(f'{int(v)}%', (yr, v), textcoords="offset points",
                    xytext=(0, 10), ha='center', color=color)

ax.axhline(100, color='red', linestyle='--', linewidth=1,
           alpha=0.5, label='100% regulatory minimum')

ax.set_xlabel('Fiscal Year')
ax.set_ylabel('Coverage Ratio (%)')
ax.legend()
ax.grid(alpha=0.3)
ax.set_xlim(2019.5, 2022.5)
ax.set_ylim(min(all_values) * 0.9, max(all_values) * 1.1)

gmcr_chg = int(cov_gmcr.diff().iloc[-1])
gpcr_chg = int(cov_gpcr.diff().iloc[-1])

insight_text = (
    f"Key Findings:\n"
    f"1. GMCR shareholder coverage improved {gmcr_chg}pp in 2021\n"
    f"2. Transition to GPCR in 2022 resulted in structurally lower ratios\n"
    f"3. GPCR shareholder coverage declined {abs(gpcr_chg)}pp in 2022 "
    f"but remains comfortably above 100%\n"
    f"4. Capital position remains robust despite volatility"
)
fig.text(0.5, -0.05, insight_text, ha='center', va='top', fontsize=9, wrap=True)

plt.tight_layout()
plt.savefig("../output_csv/charts/insight_04_capital_solvency.png", bbox_inches='tight')
print("Saved: ../output_csv/charts/insight_04_capital_solvency.png")
