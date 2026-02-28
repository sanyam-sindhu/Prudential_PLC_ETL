# Prudential PLC Annual Report ETL Pipeline

## Overview

This project pulls five key financial tables out of Prudential plc's 2021 and 2022 annual report PDFs, cleans the data, and saves everything as normalized CSV files. On top of that it generates visualizations and a set of LLM powered insights.


**Table 1 — Segment Results**
Source is IFRS note B1.1. Shows operating profit by geographic segment. Each segment has three numbers: current year AER, prior year AER, and prior year CER so you can compare growth without currency noise. Output is one row per fiscal year, line item, and basis (AER or CER).

**Table 2 — New Business Profit**
Source is the EEV results highlights section. NBP is the value created by new policies written during the year. The table has both dollar values ($m) and margin percentages, with AER and CER change columns. Output is one row per fiscal year, metric, unit, and basis.

**Table 3 — Embedded Value Movements**
Source is the movement in Group EEV shareholders' equity statement. This is an equity bridge showing how EEV changed across the year — in-force profit, new business, economic assumption changes, dividends, and forex. The 2022 PDF has 4 columns, 2021 has 5, both are mapped to the same output schema. Each line item is split into Insurance & AM, Other Central, and Group Total segments.

**Table 4 — Movement in Group Free Surplus**
Same layout as Table 3 but tracking cash and capital instead of embedded value. Shows how much free surplus was generated, consumed by new business strain, and moved by capital actions like buybacks and dividends.

**Table 5 — GWS Capital Position**
Source is the estimated GWS capital position table. Solvency figures under GMCR (2021) and GPCR (2022) — available capital, requirements, and coverage ratios split by shareholder and policyholder funds. Column count and ordering differ between the two years so each is parsed separately.



## Extraction & Cleaning Summary

**Finding the right page**

The script scans every page of both PDFs looking for a known heading like "B1.1 Segment results" or "EEV results highlights". Two things can go wrong with a naive search . the heading might appear in the table of contents, or it might appear mid-page as part of something else. To handle the first, the script checks whether the heading is followed by a page number at the end of the line (a TOC pattern) and skips it. For tables where the heading can show up in unexpected places, it also checks that the heading sits on its own line before accepting the page.

**Filtering out noise**

When pdfplumber extracts text from a page, it pulls in sidebar labels running down the margins  words like "Strategic report"  and page headers like "Prudential plc Annual Report 2022". These get mixed into the actual data lines. Before parsing anything, every line is checked against a blocklist of known sidebar words, and anything that looks like a page header gets dropped.

**Turning lines into numbers**

Each line is scanned with a regex that finds every numeric-looking token — plain numbers, numbers in brackets (negatives), percentages, percentage point changes, em dashes for blank cells, and "n/a". The positions of those tokens are recorded so the script knows exactly where the numbers start and where the label ends. The last N tokens become the data values and everything to the left becomes the row label, where N is the expected column count for that table.

**Cleaning the label**

Once the label is cut out it gets tidied up. Smart quotes are replaced with plain apostrophes. Footnote references like "note (i)" or "note (iv)" are stripped. In-text table codes like "B1.1" or "D3.5" are removed. Trailing single-digit footnote numbers at the end of a label are dropped.


**Cleaning the numbers**

Each raw token is converted to a float. Bracketed numbers like (1,234) become -1234.0. Percentage signs and "pp" suffixes are stripped (the unit is stored separately where needed). Dashes all become None. Commas and dollar signs are removed before parsing.



**Wide to long format**

Each table comes out of the PDF in wide format with a current-year column and a prior-year column. Both are unpivoted into long format so every row is one observation tagged with its fiscal year. A source report year column is kept at this stage so the dedup step knows which PDF each number came from.

**Removing duplicates**

Because each PDF has a prior-year comparison column, 2021 data appears in both the 2021 and 2022 reports. When both versions are present the script keeps the one from the more recent report — sorts by source report year descending, drops duplicates on the key columns, then removes the source year column from the final output.

**Fixing inconsistent line item names**

A handful of line items are worded differently between the two reports. These get mapped to a single label so they join cleanly across years. For example both "Shareholders' equity at beginning of year (as previously disclosed)" and "Shareholders' equity at beginning of year after adoption of HK RBC" become "Shareholders' equity at beginning of year".

---

## Insights

**Charts** — four scripts in the scripts/ folder each read a cleaned CSV and save a chart to output_csv/charts/. Geographic segment profit, new business profit with margin overlay, EEV equity bridge, and GWS solvency coverage ratios.

**LLM insights** — generate_insights_llm.py sends summary stats from all five CSVs to Groq's Llama 3.3 70B and gets back structured findings with business implications. Saved to output_csv/llm_generated_insights.json.



## How to Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Run the ETL

```bash
python etl_extract.py
```

### Charts

```bash
cd scripts
python insight_geographic_segments.py
python insight_new_business_profit.py
python insight_eev_equity_bridge.py
python insight_capital_solvency.py
```

### LLM Insights

```bash
export GROQ_API_KEY="gsk_..."
python generate_insights_llm.py
```


## Dependencies

Python 3.13, pdfplumber, pandas, matplotlib, numpy, groq
