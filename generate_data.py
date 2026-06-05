"""
Blinkit (Delhi NCR) — synthetic data generator for the GTM case study:
"Blinkit blankets core NCR. Where does the next dark store go on the NCR
growth frontier?"

IMPORTANT — this is an ILLUSTRATIVE dataset, not Blinkit's internal data
(order logs are proprietary). It is *modeled on Blinkit's real, public
footprint*: Delhi NCR is Blinkit's largest market; ~2,000+ dark stores
nationally; ~1,300 orders/store/day; net AOV ~Rs 525; the relevant tension
is new-corridor coverage gaps vs a dense, capacity-strained core.

We model a south-/east-NCR slice: 6 "anchor" coverage nodes (mature stores)
plus the newer corridors at the edge of current coverage as launch candidates.
The order table is a ~10% representative extract used for RELATIVE analysis
(demand share, growth, under-service). Absolute economics in the write-up use
Blinkit's real reported numbers.
"""

import numpy as np
import pandas as pd
from math import radians, sin, cos, asin, sqrt

rng = np.random.default_rng(42)

# ----------------------------------------------------------------------------
# 1. Existing anchor stores (mature, well-covered NCR sectors)
# ----------------------------------------------------------------------------
stores = [
    # store_id, area, pincode, lat, lng, launch_date, daily_capacity
    ("DS01", "Gurugram Cyber City", "122002", 28.4949, 77.0895, "2022-05-10", 1600),
    ("DS02", "South Delhi (Saket)", "110017", 28.5245, 77.2066, "2022-03-01", 1500),
    ("DS03", "Noida Sector 62",     "201309", 28.6271, 77.3716, "2022-08-15", 1500),
    ("DS04", "Indirapuram",         "201014", 28.6450, 77.3700, "2023-02-20", 1500),
    ("DS05", "Dwarka (Delhi)",      "110078", 28.5921, 77.0460, "2023-06-05", 1500),
    ("DS06", "Vasant Kunj",         "110070", 28.5200, 77.1591, "2023-09-12", 1400),
]
stores_df = pd.DataFrame(stores, columns=[
    "store_id", "store_area", "pincode", "lat", "lng", "launch_date", "daily_capacity_orders"])
SATURATED = {"DS04"}  # Indirapuram store runs hot -> densification signal

# ----------------------------------------------------------------------------
# 2. Areas (20). name, pincode, zone, lat, lng, households, income_idx,
#    competitors, penetration(orders/HH/month at good service), growth(monthly)
# ----------------------------------------------------------------------------
areas = [
    # --- mature / served sectors (own store) ---
    ("Gurugram Cyber City",      "122002", "Gurugram", 28.4949, 77.0895, 65000, 1.40, 4, 1.00, 1.02),
    ("South Delhi (Saket)",      "110017", "Delhi",    28.5245, 77.2066, 58000, 1.40, 3, 1.00, 1.02),
    ("Noida Sector 62",          "201309", "Noida",    28.6271, 77.3716, 60000, 1.20, 2, 0.95, 1.04),
    ("Indirapuram",              "201014", "Ghaziabad",28.6450, 77.3700, 80000, 1.10, 2, 0.95, 1.08),
    ("Dwarka (Delhi)",           "110078", "Delhi",    28.5921, 77.0460, 70000, 1.15, 2, 0.90, 1.05),
    ("Vasant Kunj",              "110070", "Delhi",    28.5200, 77.1591, 50000, 1.35, 3, 0.90, 1.02),
    # --- candidate growth-frontier corridors (no own store) ---
    ("Dwarka Expressway",        "122004", "Gurugram", 28.4500, 77.0200, 92000, 1.35, 1, 0.85, 1.12),
    ("Greater Noida West",       "201318", "Gr Noida", 28.6000, 77.4300, 95000, 1.05, 3, 0.72, 1.10),
    ("Sohna Road / SPR",         "122018", "Gurugram", 28.4600, 77.0700, 75000, 1.25, 2, 0.85, 1.10),
    ("Greater Faridabad",        "121002", "Faridabad",28.4100, 77.3300, 82000, 1.00, 1, 0.70, 1.09),
    ("Noida Sector 150",         "201310", "Noida",    28.5000, 77.4200, 52000, 1.25, 1, 0.70, 1.10),
    ("Raj Nagar Extension",      "201017", "Ghaziabad",28.7100, 77.4200, 60000, 1.00, 1, 0.65, 1.08),
    ("Noida Sector 137",         "201305", "Noida",    28.5050, 77.3900, 50000, 1.15, 2, 0.75, 1.07),
    ("New Faridabad (Sec 21)",   "121001", "Faridabad",28.4000, 77.3100, 55000, 1.00, 2, 0.70, 1.04),
    ("Greater Noida (Pari Chowk)","201310","Gr Noida", 28.4744, 77.5040, 50000, 1.00, 1, 0.60, 1.06),
    # --- near an existing store -> already well covered ---
    ("Golf Course Road",         "122002", "Gurugram", 28.4780, 77.0980, 60000, 1.40, 2, 0.95, 1.04),
    ("South Delhi (GK / CR Park)","110019","Delhi",    28.5390, 77.2410, 55000, 1.40, 3, 0.92, 1.03),
    ("Vaishali / Vasundhara",    "201012", "Ghaziabad",28.6480, 77.3450, 60000, 1.05, 2, 0.88, 1.04),
    # --- far / sparse edges ---
    ("Yamuna Expressway / Jewar","203135", "Gr Noida", 28.3000, 77.5200, 32000, 0.95, 0, 0.45, 1.07),
    ("Manesar (IMT)",            "122051", "Gurugram", 28.3540, 76.9400, 35000, 0.90, 0, 0.50, 1.06),
]
areas_df = pd.DataFrame(areas, columns=[
    "area_name", "pincode", "zone", "lat", "lng", "est_households",
    "avg_income_index", "competitor_count", "penetration_m", "growth"])

store_areas = set(stores_df["store_area"])
areas_df["has_own_store"] = areas_df["area_name"].isin(store_areas).astype(int)

# ----------------------------------------------------------------------------
# 3. Distance to nearest existing store (haversine)
# ----------------------------------------------------------------------------
def haversine(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lng2-lng1)/2)**2
    return 2 * 6371 * asin(sqrt(d))

nid, nkm = [], []
for _, a in areas_df.iterrows():
    ds = [(s.store_id, haversine(a.lat, a.lng, s.lat, s.lng)) for s in stores_df.itertuples()]
    sid, km = min(ds, key=lambda x: x[1])
    nid.append(sid); nkm.append(round(km, 2))
areas_df["nearest_store_id"] = nid
areas_df["dist_to_nearest_store_km"] = nkm

# ----------------------------------------------------------------------------
# 4. ~300k order/demand rows, Dec-2025..May-2026
# ----------------------------------------------------------------------------
months = pd.period_range("2025-12", "2026-05", freq="M")
N_ROWS = 300_000
weights, keys = [], []
for _, a in areas_df.iterrows():
    for m_idx, m in enumerate(months):
        weights.append(a.est_households * a.penetration_m * a.avg_income_index * (a.growth ** m_idx))
        keys.append((a.area_name, str(m)))
weights = np.array(weights); weights = weights / weights.sum()
draws = rng.multinomial(N_ROWS, weights)
lookup = areas_df.set_index("area_name")

rows, oid = [], 0
for (area_name, ym), n in zip(keys, draws):
    if n == 0:
        continue
    a = lookup.loc[area_name]
    period = pd.Period(ym, freq="M")
    day = rng.integers(1, period.days_in_month + 1, size=n)
    dates = pd.to_datetime([f"{ym}-{d:02d}" for d in day])
    d_km = a.dist_to_nearest_store_km
    saturated = a.nearest_store_id in SATURATED

    if d_km <= 2.5:   p, t_mu, t_sd = 0.99, 7 + 1.3*d_km, 1.6
    elif d_km <= 4.0: p, t_mu, t_sd = 0.90, 9 + 1.4*d_km, 2.2
    elif d_km <= 6.0: p, t_mu, t_sd = 0.55, 13 + 1.3*d_km, 3.0
    else:             p, t_mu, t_sd = 0.20, 16 + 1.0*d_km, 3.5
    if saturated:
        p = max(0.05, p - 0.18); t_mu += 4.0     # capacity strain at Indirapuram

    delivered = rng.random(n) < p
    other = (~delivered) & (rng.random(n) < 0.15)
    status = np.where(delivered, "delivered", np.where(other, "cancelled_other", "unserviceable"))
    dtime = np.where(delivered, np.clip(rng.normal(t_mu, t_sd, n), 5, 40).round(1), np.nan)
    promised = 12.0
    dist_arr = np.round(np.clip(rng.normal(d_km, 0.4, n), 0.2, None), 2)
    fulfilling = np.where(delivered, a.nearest_store_id, None)
    aov_mu = 430 * a.avg_income_index
    value = np.clip(rng.normal(aov_mu, 150, n), 99, 3000).round(0)

    for i in range(n):
        oid += 1
        rows.append((f"O{oid:07d}", dates[i].strftime("%Y-%m-%d"), ym, area_name, a.pincode,
                     status[i], float(value[i]),
                     None if np.isnan(dtime[i]) else float(dtime[i]),
                     promised, float(dist_arr[i]), fulfilling[i]))

orders_df = pd.DataFrame(rows, columns=[
    "order_id","order_date","order_month","area_name","pincode","status","order_value",
    "delivery_time_min","promised_time_min","dist_to_store_km","fulfilling_store_id"])

areas_out = areas_df.drop(columns=["penetration_m","growth","lat","lng"])
areas_out.to_csv("/home/claude/blinkit_areas.csv", index=False)
stores_df.to_csv("/home/claude/blinkit_dark_stores.csv", index=False)
orders_df.to_csv("/home/claude/blinkit_orders.csv", index=False)

print("areas:", areas_out.shape, "stores:", stores_df.shape, "orders:", orders_df.shape)
print("\nstatus:\n", orders_df["status"].value_counts())
print("\nblended AOV:", round(orders_df["order_value"].mean()))
print("\ncandidate distances:\n",
      areas_out[areas_out.has_own_store==0][["area_name","est_households","dist_to_nearest_store_km","nearest_store_id"]]
      .sort_values("dist_to_nearest_store_km").to_string(index=False))
