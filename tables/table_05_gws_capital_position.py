"""
Table 5: Estimated GWS Capital Position
"""

import re
import pandas as pd
from .utils import PDF_2022, PDF_2021, get_page_text, find_table_page, extract_all_tokens, parse_table_line, dedup_by_latest_report


def extract_gws_capital_position():
    all_rows=[]

    page_num=find_table_page(PDF_2022, ['Estimated GWS capital position'])
    if page_num is None:
        print("Could not find GWS capital in 2022")
    else:
        print(f"  2022: page {page_num}")
        in_table=False
        for line in get_page_text(PDF_2022, page_num).split('\n'):
            line=line.strip()
            if 'note (3)' in line.lower() and 'note (5)' in line.lower():
                in_table = True
                continue
            if not in_table:
                continue
            if line.startswith('Notes') or line.startswith('GWS sensitivity'):
                break

            all_tok = extract_all_tokens(line)
            n_tok = len(all_tok)
            if n_tok < 3:
                continue

            unit = '$bn' if '($bn)' in line else '%' if '(%)' in line else '$bn'
            result = actual_cols = None
            for try_cols in [7, 5, 3]:
                if n_tok >= try_cols:
                    result = parse_table_line(line, try_cols)
                    if result:
                        actual_cols = try_cols
                        break
            if not result:
                continue

            label, vals = result
            label = re.sub(r'\s*\(\$bn\)', '', label)
            label = re.sub(r'\s*\(%\)', '', label)
            label = label.strip()

            # most rows have the full Shareholder/Policyholder/Total split (7 cols),
            # coverage ratio rows skip Policyholder (5 cols),
            # Tier 1 rows only show a total with no split (3 cols)
            if actual_cols == 7:
                all_rows.append({
                    'Report_Year': 2022, 'Metric': label, 'Unit': unit,
                    'Shareholder_Current': vals[0], 'Policyholder_Current': vals[1], 'Total_Current': vals[2],
                    'Shareholder_Prior': vals[3], 'Policyholder_Prior': vals[4], 'Total_Prior': vals[5],
                })
            elif actual_cols == 5:
                all_rows.append({
                    'Report_Year': 2022, 'Metric': label, 'Unit': '%',
                    'Shareholder_Current': vals[0], 'Policyholder_Current': None, 'Total_Current': vals[1],
                    'Shareholder_Prior': vals[2], 'Policyholder_Prior': None, 'Total_Prior': vals[3],
                })
            elif actual_cols == 3:
                all_rows.append({
                    'Report_Year': 2022, 'Metric': label, 'Unit': unit,
                    'Shareholder_Current': None, 'Policyholder_Current': None, 'Total_Current': vals[0],
                    'Shareholder_Prior': None, 'Policyholder_Prior': None, 'Total_Prior': vals[1],
                })

    page_num = find_table_page(PDF_2021, ['Estimated GWS capital position'])
    if page_num is None:
        print("Could not find GWS capital in 2021")
    else:
        print(f"  2021: page {page_num}")
        in_table = False
        for line in get_page_text(PDF_2021, page_num).split('\n'):
            line = line.strip()
            if 'Total' in line and 'policyholder' in line and 'Shareholder' in line:
                in_table = True
                continue
            if not in_table:
                continue
            if line.startswith('Allow for') or line.startswith('Further detail'):
                break

            all_tok = extract_all_tokens(line)
            n_tok = len(all_tok)
            if n_tok < 4:
                continue

            unit = '$bn' if '($bn)' in line else '%' if '(%)' in line else '$bn'
            result = parse_table_line(line, n_tok)
            if not result:
                continue
            label, vals = result
            label = re.sub(r'\s*\(\$bn\)', '', label)
            label = re.sub(r'\s*\(%\)', '', label)
            label = label.strip()

            # 2021 column order is flipped: Total comes first, then Policyholder, then Shareholder
            if n_tok >= 6:
                all_rows.append({
                    'Report_Year': 2021, 'Metric': label, 'Unit': unit,
                    'Total_Current': vals[0], 'Policyholder_Current': vals[1], 'Shareholder_Current': vals[2],
                    'Total_Prior': vals[3], 'Policyholder_Prior': vals[4], 'Shareholder_Prior': vals[5],
                })
            elif n_tok == 4:
                all_rows.append({
                    'Report_Year': 2021, 'Metric': label, 'Unit': '%',
                    'Total_Current': vals[0], 'Policyholder_Current': None, 'Shareholder_Current': vals[1],
                    'Total_Prior': vals[2], 'Policyholder_Prior': None, 'Shareholder_Prior': vals[3],
                })

    df = pd.DataFrame(all_rows)
    print(f"   {len(df)} rows")
    return df


def normalize_gws_capital(df):
    """unpivots gws capital position to long format"""
    rows = []
    for _, r in df.iterrows():
        ry = int(r['Report_Year'])
        m, u = r['Metric'], r['Unit']
        for period, suffix in [('Current', ry), ('Prior',ry-1)]:
            for cat in ['Shareholder', 'Policyholder', 'Total']:
                col = f'{cat}_{period}'
                if col in r.index:
                    rows.append({'Fiscal_Year': suffix, 'Metric': m, 'Unit': u, 'Category': cat, 'Value': r[col], 'Source_Report_Year': ry})
    long = pd.DataFrame(rows)
    return dedup_by_latest_report(long, ['Fiscal_Year', 'Metric', 'Unit', 'Category'])
