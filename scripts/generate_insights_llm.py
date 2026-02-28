import os, json
import pandas as pd
from groq import Groq

OUTPUT_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output_csv")
TABLES = {
    "Segment Results":           "01_segment_results.csv",
    "New Business Profit (EEV)": "02_new_business_profit.csv",
} ## due to limitation in tokens sending less table data

client =Groq(api_key=os.environ["GROQ_API_KEY"])

data = []
for name, fname in TABLES.items():
    df =pd.read_csv(os.path.join(OUTPUT_DIR, fname))
    idx =next(c for c in df.columns if c != "Fiscal_Year" and not pd.api.types.is_numeric_dtype(df[c]))
    val= next(c for c in df.columns if c != "Fiscal_Year" and pd.api.types.is_numeric_dtype(df[c]))
    pivot= df.pivot_table(index=idx, columns="Fiscal_Year", values=val, aggfunc="sum")
    pivot.columns=[str(c) for c in pivot.columns]
    data.append(f"### {name}\n{pivot.to_string()}")

r = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": (
            "You are a senior financial analyst specialising in insurance and embedded value reporting. "
            "You are analysing Prudential plc's performance across fiscal years 2020, 2021, and 2022. "
            "Your insights must be data-driven, specific, and actionable. "
            "Always cite exact numbers and year-over-year percentage changes. "
            "Never introduce figures that are not present in the data provided. "
            "Each insight should tell a clear story: what happened, why it matters, and what it signals."
        )},
        {"role": "user",   "content": f"Data:\n{chr(10).join(data)}\n\nReturn JSON: {{\"insights\": [{{title, finding, implication, supporting_data, suggested_viz}}]}} — exactly 2 insights, one per table, only use numbers from the data above."},
    ],
    temperature=0.2,
    response_format={"type": "json_object"},
)

insights = json.loads(r.choices[0].message.content)["insights"]
json.dump(insights, open(os.path.join(OUTPUT_DIR, "llm_generated_insights.json"), "w"), indent=2)
