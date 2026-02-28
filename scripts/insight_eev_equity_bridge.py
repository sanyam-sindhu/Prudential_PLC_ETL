"""
 EEV Shareholders Equity Analysis
Two views: operating vs non-operating split, and equity bridge.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("../output_csv/03_embedded_value_movements.csv")
gt = df[df.Segment == 'Group_Total'].copy()

def get(year, item):
    fy = gt[gt.Fiscal_Year == year].set_index('Line_Item')['Value_$m']
    return fy.get(item, 0)

years = [2020, 2021, 2022]

op_profit = [get(y, 'Operating profit (loss) for the year') for y in years]
non_op = [get(y, 'Non-operating results') for y in years]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("EEV Shareholders' Equity Analysis (2020-2022)", fontsize=16, y=0.98)

x = np.arange(len(years))
bars_op = ax1.bar(x, [v/1000 for v in op_profit], 0.5, color='blue', label='Operating')
non_op_colors = ['green' if v >= 0 else 'red' for v in non_op]
bars_no = ax1.bar(x, [v/1000 for v in non_op], 0.5, bottom=[v/1000 for v in op_profit],
                  color=non_op_colors, label='Non-operating')
ax1.bar_label(bars_op, labels=[f'{v/1000:.1f}bn' for v in op_profit], padding=3)
ax1.bar_label(bars_no, labels=[f'{v/1000:.1f}bn' for v in non_op], padding=3)
ax1.set_title("Operating vs Non-operating Profit")
ax1.set_xticks(x)
ax1.set_xticklabels([str(y) for y in years])
ax1.set_ylabel('USD bn')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)
ax1.axhline(0, color='black', linewidth=0.5)

#Subplot 2: Equity Bridge
fy22 = gt[gt.Fiscal_Year == 2022].set_index('Line_Item')['Value_$m']
opening = fy22.get("Shareholders' equity at beginning of year (as previously disclosed)", 0)
closing = fy22.get("Shareholders' equity at end of year", 0)

items = [
    ("Op. profit",   fy22.get("Operating profit (loss) for the year", 0)),
    ("Inv. fluct.",   fy22.get("Short-term fluctuations in investment returns", 0)),
    ("Econ. assum.",  fy22.get("Effect of changes in economic assumptions", 0)),
    ("FX moves",      fy22.get("Foreign exchange movements on operations", 0)),
    ("Div. & other",  fy22.get("Other external dividends", 0)
                      + fy22.get("Other movements", 0)
                      + fy22.get("New share capital subscribed", 0)),
]

labels = ["Opening"] + [i[0] for i in items] + ["Closing"]
values = [opening] + [i[1] for i in items] + [closing]

cumulative = [opening]
for _, v in items:
    cumulative.append(cumulative[-1] + v)

bottoms, heights, bar_colors = [], [], []
for i, val in enumerate(values):
    if i == 0:
        bottoms.append(0); heights.append(val); bar_colors.append('blue')
    elif i == len(values) - 1:
        bottoms.append(0); heights.append(val); bar_colors.append('darkblue')
    elif val >= 0:
        bottoms.append(cumulative[i-1]); heights.append(val); bar_colors.append('green')
    else:
        bottoms.append(cumulative[i-1]+val); heights.append(abs(val)); bar_colors.append('red')

xw = np.arange(len(labels))
bars_w = ax2.bar(xw, heights, bottom=bottoms, color=bar_colors, width=0.6)

for i, (bar, val) in enumerate(zip(bars_w, values)):
    if i == 0 or i == len(labels) - 1:
        text, va = f'{val/1000:.1f}bn', 'bottom'
    elif val >= 0:
        text, va = f'+{val/1000:.1f}bn', 'bottom'
    else:
        text, va = f'{val/1000:.1f}bn', 'top'
    y = bar.get_y() + bar.get_height() if va == 'bottom' else bar.get_y()
    ax2.text(bar.get_x() + bar.get_width()/2, y, text, ha='center', va=va)

for i in range(len(labels) - 1):
    y = cumulative[0] if i == 0 else cumulative[i]
    ax2.plot([xw[i]+0.32, xw[i+1]-0.32], [y, y], color='grey', lw=0.7, ls='--')

ax2.set_title("Equity Bridge FY2022")
ax2.set_xticks(xw)
ax2.set_xticklabels(labels)
ax2.set_ylabel('USD m')
ax2.grid(axis='y', alpha=0.2)
ax2.set_ylim(0, opening * 1.15)


equity_drop = closing - opening
insight_text = (
    f"Insights:\n"
    f"1. Operating profit grew steadily ({op_profit[0]/1000:.1f}bn to {op_profit[2]/1000:.1f}bn) "
    f"but 2022 non-operating losses of {abs(non_op[2])/1000:.1f}bn wiped out all gains\n"
    f"2. EEV equity fell {abs(equity_drop)/1000:.1f}bn in 2022 despite record operating profit\n"
    f"3. Investment fluctuations ({items[1][1]/1000:.1f}bn) were the single largest drag"
)
fig.text(0.5, -0.04, insight_text, ha='center', va='top', fontsize=9, wrap=True)

plt.tight_layout()
plt.savefig("../output_csv/charts/insight_03_eev_equity_bridge.png", bbox_inches='tight')
print("Saved: ../output_csv/charts/insight_03_eev_equity_bridge.png")
