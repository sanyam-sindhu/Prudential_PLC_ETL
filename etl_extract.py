"""
ETL pipeline for Prudential PLC annual reports (2021 & 2022)
extracts 5 financial tables from PDFs into normalized CSV files
"""

import os
from tables.utils import OUTPUT_DIR, normalize_4col_table
from tables.table_01_segment_results import extract_segment_results, normalize_segment_results
from tables.table_02_new_business_profit import extract_new_business_profit, normalize_new_business_profit
from tables.table_03_embedded_value_movements import extract_embedded_value_movements
from tables.table_04_free_surplus_movement import extract_free_surplus_movement
from tables.table_05_gws_capital_position import extract_gws_capital_position, normalize_gws_capital


if __name__== "__main__":
    print("Prudential Annual Report ETL Pipeline\n")

    tables = [
        ("01_segment_results.csv", extract_segment_results, normalize_segment_results),
        ("02_new_business_profit.csv", extract_new_business_profit, normalize_new_business_profit),
        ("03_embedded_value_movements.csv", extract_embedded_value_movements, normalize_4col_table),
        ("04_movement_group_free_surplus.csv", extract_free_surplus_movement, normalize_4col_table),
        ("05_gws_capital_position_solvency.csv", extract_gws_capital_position, normalize_gws_capital),
    ]

    for filename, extract_fn, normalize_fn in tables:
        df_wide = extract_fn()
        df_long = normalize_fn(df_wide)
        path = os.path.join(OUTPUT_DIR, filename)
        df_long.to_csv(path, index=False)
        print(f"  Saved: {filename} ({len(df_long)} rows)\n")

    print("CSVs saved to:", OUTPUT_DIR)
