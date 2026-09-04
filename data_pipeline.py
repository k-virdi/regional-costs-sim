import pandas as pd
import numpy as np
import sqlite3
import os

DB_PATH = "census_data.db"

def generate_mock_data():
    np.random.seed(42)
    regions = [
        "New York", "California", "Texas",   # US
        "Ontario", "Quebec", "British Columbia"  # Canada
    ]
    years = list(range(1975, 2026))  # 50 years

    data = []
    for region in regions:
        # base values in 1975 (in USD for US, CAD for CA – we keep all in USD for simplicity)
        if region in ["New York", "California", "Texas"]:
            base_income = 15000 + np.random.randint(-2000, 2000)
            base_rent = 300 + np.random.randint(-50, 50)
            base_taxes = 2000 + np.random.randint(-300, 300)
            grocery_base = 80
        else:  # Canada
            base_income = 12000 + np.random.randint(-2000, 2000)
            base_rent = 250 + np.random.randint(-50, 50)
            base_taxes = 1500 + np.random.randint(-300, 300)
            grocery_base = 70

        # random growth factors
        income_growth = np.random.uniform(0.02, 0.045)
        rent_growth = np.random.uniform(0.025, 0.05)
        tax_growth = np.random.uniform(0.015, 0.04)
        grocery_growth = np.random.uniform(0.01, 0.035)

        for year in years:
            t = year - 1975
            # add some noise
            income = base_income * (1 + income_growth) ** t + np.random.normal(0, 500)
            rent = base_rent * (1 + rent_growth) ** t + np.random.normal(0, 20)
            taxes = base_taxes * (1 + tax_growth) ** t + np.random.normal(0, 100)
            grocery = grocery_base * (1 + grocery_growth) ** t + np.random.normal(0, 2)

            data.append({
                "region": region,
                "year": year,
                "median_income": max(0, round(income, 0)),
                "median_rent": max(0, round(rent, 0)),
                "avg_taxes": max(0, round(taxes, 0)),
                "grocery_index": round(max(50, grocery), 1)   # index relative to avg
            })

    return pd.DataFrame(data)

def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # fresh start

    df = generate_mock_data()
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("census_data", conn, if_exists="replace", index=False)
    conn.close()
    print(f"✅ Database created with {len(df)} records.")

if __name__ == "__main__":
    build_database()
