"""
Table 2: EEV New Business Profit Highlights
"""

import re
import pandas as pd
from .utils import PDF_2022, PDF_2021, get_page_text, find_table_page, _extract_rows, dedup_by_latest_report


def _schema_nbp(_year, num_cols, label, vals, raw):
    """maps new business profit columns, detects % vs $m unit from the raw line"""
    unit= '%' if '(%)' in raw or (num_cols < 5 and '%' in raw) else '$m'
    return {
        'Metric': label.replace('(%)', '').strip(),
        'Unit': unit,
        'Current_Year_AER': vals[0] if len(vals) > 0 else None,
        'Prior_Year_AER': vals[1] if len(vals) > 1 else None,
        'Change_AER_pct': vals[2] if len(vals) > 2 else None,
        'Prior_Year_CER': vals[3] if len(vals) > 3 else None,
        'Change_CER_pct': vals[4] if len(vals) > 4 else None,
    }


def extract_new_business_profit():
    all_rows=[]

    def _nbp_start(line):
        if '% change' in line and '$m' in line:
            return True
        if re.match(r'^note\s*\(', line, re.IGNORECASE):
            inner=re.sub(r'note\s*|\(|\)', '', line, flags=re.IGNORECASE).strip()
            if not any(c.isdigit() for c in inner):
                return True
        return False

    def _nbp_end(line):
        return (line.startswith('Notes')
                or line.startswith('* Re-presented')
                or line.startswith('The EEV'))

    for pdf_path, year in [(PDF_2022, 2022), (PDF_2021, 2021)]:
        page_num=find_table_page(pdf_path, ['EEV results highlights'])
        if page_num is None:
            print(f"Could not find EEV highlights in {year}")
            continue
        print(f"  {year}: page {page_num}")
        lines = get_page_text(pdf_path, page_num).split('\n')
        all_rows.extend(_extract_rows(
            lines, year, 5,
            start_fn=_nbp_start,
            end_fn=_nbp_end,
            skip_fn=lambda l: False,
            schema_fn=_schema_nbp,
            allow_partial=True,
            partial_max_tokens=1,
        ))



    df = pd.DataFrame(all_rows)
    print(f"{len(df)} rows")
    return df


def normalize_new_business_profit(df):
    rows=[]
    for _, r in df.iterrows():
        ry=int(r['Report_Year'])
        m,u =r['Metric'], r['Unit']
        rows.append({'Fiscal_Year': ry, 'Metric': m, 'Unit': u, 'Basis': 'AER', 'Value': r['Current_Year_AER'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry-1, 'Metric': m, 'Unit': u, 'Basis': 'AER', 'Value': r['Prior_Year_AER'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry-1, 'Metric': m, 'Unit': u, 'Basis': 'CER', 'Value': r['Prior_Year_CER'], 'Source_Report_Year': ry})
    long = pd.DataFrame(rows)
    return dedup_by_latest_report(long, ['Fiscal_Year', 'Metric', 'Unit', 'Basis'])
