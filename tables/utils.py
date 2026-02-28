"""
Shared utilities, constants, and helpers used by all table .
"""

import pdfplumber
import pandas as pd
import re
import os

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR=os.path.join(BASE_DIR, "output_csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PDF_2022=os.path.join(BASE_DIR, "data", "prudential-plc-ar-2022.pdf")
PDF_2021=os.path.join(BASE_DIR, "data", "prudential-plc-ar-2021.pdf")

SIDEBAR_NOISE={
    'Group','overview', 'Strategic', 'report','Governance','Directors\u2019','remuneration','Financial', 'statements', 'European', 'Embedded',
    'Value','(EEV)', 'basis', 'results', 'Additional', 'information',
}


def get_page_text(pdf_path, page_num):
    """pulls text from a single page """
    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[page_num - 1].extract_text() or ''


def get_pages_text(pdf_path, page_nums):
    """pulls and joins text from multiple pages"""
    with pdfplumber.open(pdf_path) as pdf:
        return '\n'.join(pdf.pages[p - 1].extract_text() or '' for p in page_nums)


def clean_number(val):
    """converts a raw pdf token to float, returns none for blanks/dashes/n/a"""
    if val is None:
        return None
    val = str(val).strip()
    if val in ('', '\u2014', '\u2013', '\ufffd', 'n/a', '*'):
        return None
    val = val.replace('*', '').strip()
    val = val.replace('%', '').replace('pp', '').strip()
    val = val.replace('\u00a2', '').strip()
    if val.startswith('(') and val.endswith(')'):
        val = '-' + val[1:-1]
    val = val.replace(',', '').replace('$', '').strip()
    if val in ('', '\u2014', '\u2013', '\ufffd'):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def extract_all_tokens(line):
    pattern = r'(\([0-9,]+(?:\.[0-9]+)?\)%?|[0-9,]+(?:\.[0-9]+)?%?(?:pp)?|n/a|[\ufffd\u2014\u2013]|\+[0-9]+(?:pp|%))'
    return [(m.group(), m.start(), m.end()) for m in re.finditer(pattern, line)]


def parse_table_line(line, expected_cols):
    """splits a line into a label and the last n numeric values"""
    all_tokens = extract_all_tokens(line)
    if len(all_tokens) < expected_cols:
        return None

    data_block =all_tokens[-expected_cols:]
    label_end =data_block[0][1]
    if label_end<= 0:
        return None

    label=line[:label_end].strip()
    label=label.replace('\u2019', "'").replace('\u2018', "'")
    label=re.sub(r'\s*notes?\s*\([ivx\d]+\)(\([ivx\d]+\))*', '', label, flags=re.IGNORECASE)
    label=re.sub(r'\s+[BDC]\d+(?:\.\d+)?', '', label)
    label=re.sub(r'\s+\d{1,2}$', '', label)
    label=label.strip()

    values=[clean_number(t[0]) for t in data_block]
    return (label, values)


def is_noise_line(line):
    """returns true if the line is a sidebar label or page footer we should ignore"""
    stripped =line.strip()
    if stripped in SIDEBAR_NOISE:
        return True
    if stripped.startswith('Prudential plc') and ('Annual Report' in stripped or len(stripped) < 30):
        return True
    if re.match(r'^\d+\s+Prudential plc', stripped):
        return True
    return False


_PAGE_CACHE: dict ={}


def _get_page_texts(pdf_path):
    """returns all page texts for a pdf, cached so we only open it once"""
    if pdf_path not in _PAGE_CACHE:
        with pdfplumber.open(pdf_path) as pdf:
            _PAGE_CACHE[pdf_path] =[p.extract_text() or '' for p in pdf.pages]
    return _PAGE_CACHE[pdf_path]


def _is_toc_reference(page_text, marker):
    """checks if the marker only appears as a toc entry rather than an actual table heading"""
    lines = page_text.split('\n')
    first = lines[0].strip().lower()
    header = ' '.join(lines[:5]).lower()
    if first.startswith('index') or any(kw in header for kw in ('contents', 'table of contents')):
        return True
    for line in lines:
        if marker.lower() in line.lower():
            if re.search(r'\s+\d{2,3}\s*$', line.rstrip()):
                return True
    return False


def _marker_is_heading(page_text, marker):
    for line in page_text.split('\n'):
        if line.strip().lower() ==marker.lower():
            return True
    return False


def find_table_page(pdf_path, markers, context_required=None, heading_required=False):
    """scans the whole pdf and returns the page number where the table heading is found"""
    for i, text in enumerate(_get_page_texts(pdf_path)):
        for marker in markers:
            if marker.lower() in text.lower():
                if not _is_toc_reference(text, marker):
                    if context_required is None or all(
                        ctx.lower() in text.lower() for ctx in context_required
                    ):
                        if not heading_required or _marker_is_heading(text, marker):
                            return i + 1
    return None


def _extract_rows(lines, report_year, num_cols,
                  start_fn, end_fn, skip_fn, schema_fn,
                  allow_partial=False, partial_max_tokens=0):
    """parses lines into row dicts using start/end/skip signals and a schema mapper"""
    rows = []
    in_data = False
    prev_partial = None

    for raw_line in lines:
        line = raw_line.strip()
        if is_noise_line(line):
            continue

        if in_data and end_fn(line):
            break

        if not in_data:
            if start_fn(line):
                in_data = True
            continue

        if start_fn(line) or not line or skip_fn(line):
            continue

        all_tok = extract_all_tokens(line)
        n_tok = len(all_tok)

        if n_tok >= num_cols:
            result = parse_table_line(line, num_cols)
            if result:
                label, vals = result
                if prev_partial:
                    label = (prev_partial + ' ' + label).strip() if label else prev_partial
                    prev_partial = None
                if label:
                    row = schema_fn(report_year, num_cols, label, vals, line)
                    if row is not None:
                        rows.append({'Report_Year': report_year, **row})
                continue

        if allow_partial and n_tok >= 2:
            result = parse_table_line(line, n_tok)
            if result:
                label, vals = result
                if prev_partial:
                    label = (prev_partial + ' ' + label).strip() if label else prev_partial
                    prev_partial = None
                if label:
                    row = schema_fn(report_year, n_tok, label, vals, line)
                    if row is not None:
                        rows.append({'Report_Year': report_year, **row})
                continue

        if (n_tok <= partial_max_tokens and line
                and not line.startswith('(')
                and not re.match(r'^\d{4}\b', line)):
            prev_partial = line if not prev_partial else prev_partial + ' ' + line
        else:
            prev_partial = None

    return rows


def dedup_by_latest_report(df, key_cols, value_col='Value'):
    """keeps the latest report version when the same data point appears in multiple years"""
    df=df.dropna(subset=[value_col])
    df=df.sort_values('Source_Report_Year', ascending=False)
    df= df.drop_duplicates(subset=key_cols, keep='first')
    df=df.drop(columns=['Source_Report_Year'])
    return df.sort_values(key_cols).reset_index(drop=True)


# shared by tables 3 and 4

def _schema_4col(_year, num_cols, label, vals, _raw):
    """maps 4 or 5 column eev/free surplus rows, skipping the cer sub-total in the 5-col layout"""
    if num_cols == 4:
        return {
            'Line_Item': label,
            'Insurance_and_AM_Operations_$m': vals[0],
            'Other_Central_Operations_$m': vals[1],
            'Group_Total_$m': vals[2],
            'Group_Prior_Year_$m': vals[3],
        }
    return {
        'Line_Item': label,
        'Insurance_and_AM_Operations_$m': vals[0],
        'Other_Central_Operations_$m': vals[1],
        'Group_Total_$m': vals[3],
        'Group_Prior_Year_$m': vals[4],
    }


def normalize_4col_table(df):
    rows = []
    for _, r in df.iterrows():
        ry=int(r['Report_Year'])
        li=r['Line_Item']
        rows.append({'Fiscal_Year': ry,'Line_Item': li, 'Segment': 'Insurance_and_AM', 'Value_$m': r['Insurance_and_AM_Operations_$m'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry,'Line_Item': li, 'Segment': 'Other_Central', 'Value_$m': r['Other_Central_Operations_$m'], 'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry,'Line_Item': li, 'Segment': 'Group_Total', 'Value_$m': r['Group_Total_$m'],'Source_Report_Year': ry})
        rows.append({'Fiscal_Year': ry-1,'Line_Item': li, 'Segment': 'Group_Total', 'Value_$m': r['Group_Prior_Year_$m'], 'Source_Report_Year': ry})
    long = pd.DataFrame(rows)
    long['Line_Item'] = long['Line_Item'].replace({
        'Non-operating profit (loss)': 'Non-operating results',
        'Profit from in-force long-term business': 'Profit from in-force business',
        "Shareholders' equity at beginning of year (as previously disclosed)": "Shareholders' equity at beginning of year",
        "Shareholders' equity at beginning of year after adoption of HK RBC": "Shareholders' equity at beginning of year",
    })
    return dedup_by_latest_report(long, ['Fiscal_Year', 'Line_Item', 'Segment'], 'Value_$m')
