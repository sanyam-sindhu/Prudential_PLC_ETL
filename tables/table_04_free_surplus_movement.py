"""
Table 4: Movement in Group Free Surplus
"""

import re
import pandas as pd
from .utils import PDF_2022, PDF_2021, get_pages_text, find_table_page, _extract_rows, _schema_4col


def extract_free_surplus_movement():
    all_rows = []
    col_map = {2022: 4, 2021: 5}
    _SKIP = frozenset({
        'Continuing operations:',
        'Equity items from continuing operations:',
        'Representing:',
    })

    for pdf_path, year in [(PDF_2022, 2022), (PDF_2021, 2021)]:
        page_num = find_table_page(
            pdf_path, ['Movement in Group free surplus'],
            heading_required=True,
        )
        if page_num is None:
            print(f"Could not find free surplus in {year}")
            continue
        num_cols=col_map[year]
        print(f"  {year}: pages {page_num}-{page_num + 1}")
        lines=get_pages_text(pdf_path, [page_num, page_num + 1]).split('\n')
        all_rows.extend(_extract_rows(
            lines, year, num_cols,
            start_fn=lambda l: 'operations' in l.lower() and 'total' in l.lower(),
            end_fn=lambda l: (l.startswith('Notes') and len(l) < 10) or 'Contribution to Group' in l,
            skip_fn=lambda l: l in _SKIP or bool(re.match(r'^Note\s+note', l, re.IGNORECASE)),
            schema_fn=_schema_4col,
            partial_max_tokens=1,
        ))

    df = pd.DataFrame(all_rows)
    print(f"{len(df)} rows")
    return df
