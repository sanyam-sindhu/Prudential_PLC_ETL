"""
Table 1: B1.1 Segment Results
"""

import pandas as pd
from .utils import PDF_2022, PDF_2021, get_page_text, find_table_page, _extract_rows, dedup_by_latest_report


def _schema_segment(_year, _num_cols, label, vals, _raw):
    """maps segment results columns to a dict"""
    return {
        'Line_Item': label,
        'AER_Current_Year_$m': vals[0],
        'AER_Prior_Year_$m': vals[1],
        'CER_Prior_Year_$m': vals[2],
    }
def extract_segment_results():
    all_rows = []
    NUM_COLS = 5
    _SKIP = frozenset({
        'Other income and expenditure unallocated to a segment:',
        'Other income and expenditure:',
    })

    for pdf_path, year in [(PDF_2022, 2022), (PDF_2021, 2021)]:
        page_num = find_table_page(pdf_path, ['B1.1 Segment results'])
        if page_num is None:
            print(f"Could not find B1.1 in {year}")
            continue
        print(f"  {year}: page {page_num}")
        lines = get_page_text(pdf_path, page_num).split('\n')
        all_rows.extend(_extract_rows(
            lines, year, NUM_COLS,
            start_fn=lambda l: 'Continuing operations:' in l,
            end_fn=lambda l: l == 'Attributable to:',
            skip_fn=lambda l: l in _SKIP,
            schema_fn=_schema_segment,
        ))

    df = pd.DataFrame(all_rows)
    return df


def normalize_segment_results(df):
    rows = []
    for _, r in df.iterrows():
        ry=int(r['Report_Year'])
        li=r['Line_Item']
        rows.append({'Fiscal_Year': ry,'Line_Item': li, 'Basis': 'AER', 'Value_$m': r['AER_Current_Year_$m'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry-1, 'Line_Item': li, 'Basis': 'AER', 'Value_$m': r['AER_Prior_Year_$m'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry-1, 'Line_Item': li, 'Basis': 'CER', 'Value_$m': r['CER_Prior_Year_$m'], 'Source_Report_Year': ry})
    long = pd.DataFrame(rows)
    return dedup_by_latest_report(long, ['Fiscal_Year', 'Line_Item', 'Basis'], 'Value_$m')
