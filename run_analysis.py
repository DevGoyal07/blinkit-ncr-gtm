"""Load the CSVs into an in-memory SQLite DB, run each named query block from
analysis.sql, and print the results as clean tables."""
import re, sqlite3, pandas as pd

con = sqlite3.connect(":memory:")
for tbl, path in [("areas","blinkit_areas.csv"),
                  ("dark_stores","blinkit_dark_stores.csv"),
                  ("orders","blinkit_orders.csv")]:
    pd.read_csv(f"/home/claude/{path}").to_sql(tbl, con, index=False, if_exists="replace")

sql = open("/home/claude/analysis.sql").read()
blocks = re.split(r"-- @@QUERY:\s*(\w+)\s*--\s*(.*)", sql)
for i in range(1, len(blocks), 3):
    name, desc, body = blocks[i], blocks[i+1].strip(), blocks[i+2]
    df = pd.read_sql_query(body, con)
    print("\n" + "="*100)
    print(f"[{name}]  {desc}")
    print("="*100)
    with pd.option_context("display.max_columns", None, "display.width", 220):
        print(df.to_string(index=False))
