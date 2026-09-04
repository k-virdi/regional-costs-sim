from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Optional

app = FastAPI()

# serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = "census_data.db"

@app.get("/api/regions")
def get_regions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT DISTINCT region FROM census_data ORDER BY region", conn)
    conn.close()
    return {"regions": df["region"].tolist()}

@app.get("/api/data")
def get_data(
    regions: Optional[List[str]] = Query(None),
    year_min: int = Query(1975, ge=1975, le=2025),
    year_max: int = Query(2025, ge=1975, le=2025)
):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM census_data WHERE year BETWEEN ? AND ?"
    params = [year_min, year_max]
    if regions:
        placeholders = ",".join(["?"] * len(regions))
        query += f" AND region IN ({placeholders})"
        params.extend(regions)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/api/simulate")
def simulate_policy(
    region: str,
    tax_change_pct: float = Query(..., description="% change in tax (e.g., -5 for 5% cut)"),
    year: int = Query(2025)
):
    """
    Simple game-theory simulation: 
    - Higher taxes reduce affordability, causing population outflow.
    - Lower taxes improve affordability, attracting population.
    We return a predicted 'affordability_index' and 'population_shift' (in %).
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM census_data WHERE region = ? AND year = ?",
        conn,
        params=[region, year]
    )
    conn.close()
    if df.empty:
        return {"error": "No data for that region/year"}

    row = df.iloc[0]
    base_taxes = row["avg_taxes"]
    base_income = row["median_income"]
    base_rent = row["median_rent"]

    # new tax amount
    new_tax = base_taxes * (1 + tax_change_pct / 100)
    # affordability = (income - rent - tax) / cost_of_living (simplified)
    # we use grocery_index as a proxy for cost of living
    cost_of_living = row["grocery_index"] * 1.0
    base_affordability = (base_income - base_rent - base_taxes) / cost_of_living
    new_affordability = (base_income - base_rent - new_tax) / cost_of_living

    # population shift: people move to regions with better affordability.
    # using a logistic function to simulate migration
    delta = new_affordability - base_affordability
    # if delta > 0, population increases, else decreases
    # scale: a 10% improvement in affordability -> ~5% population growth
    pop_shift_pct = np.tanh(delta / (base_affordability * 0.5)) * 10

    return {
        "region": region,
        "year": year,
        "tax_change_pct": tax_change_pct,
        "base_affordability": round(base_affordability, 2),
        "new_affordability": round(new_affordability, 2),
        "population_shift_pct": round(pop_shift_pct, 2),
        "new_tax": round(new_tax, 0)
    }

# root returns the frontend
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("static/index.html", "r") as f:
        return f.read()
