"""
GridGuard AI - Realistic Demonstration Data Generator
=====================================================
WARNING: THIS IS SYNTHETIC DEMONSTRATION DATA FOR PROTOTYPING ONLY.
         NOT REAL UTILITY DATA. FOR HACKATHON / EDUCATIONAL USE.

Generated datasets:
  1. data/assets.csv           - ~100 grid assets (Transformers, Substations)
  2. data/sensor_readings.csv  - ~5000 time-series sensor readings
  3. data/incidents.csv        - Historical failure & outage incidents
  4. data/weather.csv          - Multi-region weather observations
  5. data/crews.csv            - Field maintenance crews

Logical relationships enforced:
  * Older assets -> higher historical failures, lower health scores
  * High-capacity assets -> serve more customers & critical facilities
  * Low health score -> abnormal temp/vibration/oil/partial_discharge
  * High load% -> elevated temperature & current
  * Severe weather (high wind/rain) -> higher storm_risk, weather-related incidents
  * Incident severity -> correlated with repair cost, customers affected, duration
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================
SEED = 42
np.random.seed(SEED)

NUM_ASSETS = 100
NUM_READINGS_PER_ASSET = 50  # ~5000 total readings
NUM_INCIDENTS = 150
NUM_WEATHER_RECORDS = 800
NUM_CREWS = 7

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Geographic regions (roughly NYC metro area for consistency)
REGIONS = [
    {"name": "North District",   "lat": 40.8000, "lon": -73.9500},
    {"name": "Eastside",         "lat": 40.7500, "lon": -73.9200},
    {"name": "Downtown",         "lat": 40.7100, "lon": -74.0100},
    {"name": "Westside",         "lat": 40.7600, "lon": -73.9900},
    {"name": "South District",   "lat": 40.6800, "lon": -74.0000},
    {"name": "Central",          "lat": 40.7500, "lon": -73.9800},
    {"name": "Riverside Area",   "lat": 40.7800, "lon": -73.9700},
    {"name": "Industrial Park",  "lat": 40.7000, "lon": -73.9000},
]

ASSET_TYPES = ["Transformer", "Substation"]

INCIDENT_TYPES = [
    "Transformer Overheating",
    "Insulation Failure",
    "Voltage Sag/Swell",
    "Conductor Damage",
    "Lightning Strike",
    "Oil Leak",
    "Breaker Malfunction",
    "Load Overload",
    "Tree Contact",
    "Equipment Aging",
]

SEVERITIES = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = [0.35, 0.35, 0.20, 0.10]


# ============================================================
# HELPER: Clip values to realistic ranges
# ============================================================
def clip(val, lo, hi):
    if lo is not None and val < lo:
        return lo
    if hi is not None and val > hi:
        return hi
    return val


# ============================================================
# 1. GENERATE ASSETS
# ============================================================
print("[1/5] Generating assets.csv ...")

assets_list = []

for i in range(1, NUM_ASSETS + 1):
    asset_type = np.random.choice(ASSET_TYPES, p=[0.70, 0.30])

    region = REGIONS[np.random.randint(0, len(REGIONS))]
    jitter_lat = np.random.uniform(-0.02, 0.02)
    jitter_lon = np.random.uniform(-0.02, 0.02)

    substation_num = (i % 12) + 1
    substation_id = f"SUB-{substation_num:03d}"

    installation_year = int(np.random.choice(
        [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020],
        p=[0.05, 0.08, 0.12, 0.15, 0.18, 0.18, 0.15, 0.09]
    ))
    age_years = 2026 - installation_year

    # Capacity: substations usually bigger than transformers
    if asset_type == "Substation":
        capacity_mva = round(float(np.random.choice(
            [50, 75, 100, 150, 200, 300],
            p=[0.10, 0.20, 0.25, 0.25, 0.15, 0.05]
        )), 1)
    else:
        capacity_mva = round(float(np.random.choice(
            [5, 10, 15, 25, 40, 60, 75],
            p=[0.15, 0.25, 0.20, 0.18, 0.12, 0.07, 0.03]
        )), 1)

    # Customers served scales with capacity, plus some noise
    customers_served = int(clip(
        (capacity_mva * 420) + np.random.normal(0, capacity_mva * 80),
        50, 50000
    ))

    # Critical facilities (hospitals, data centers, etc.) also scale
    critical_facility_count = int(clip(
        round(customers_served / 4500 + np.random.poisson(1.2)),
        0, 25
    ))

    # Historical failures: strongly correlated with age, weak with capacity
    age_factor = (age_years / 40) ** 1.5
    hist_fail = int(clip(
        round(np.random.poisson(0.3 + age_factor * 3.2 + capacity_mva * 0.008)),
        0, 25
    ))

    # Current health score: 100 = perfect, 0 = dead
    # Driven down by: age, historical failures, random noise
    health_penalty_age = age_years * 0.9
    health_penalty_fail = hist_fail * 3.2
    health_noise = np.random.normal(0, 6.0)
    current_health_score = int(clip(
        95 - health_penalty_age - health_penalty_fail - health_noise,
        8, 100
    ))

    asset = {
        "asset_id": f"AST-{i:04d}",
        "asset_type": asset_type,
        "substation_id": substation_id,
        "location": region["name"],
        "latitude": round(region["lat"] + jitter_lat, 6),
        "longitude": round(region["lon"] + jitter_lon, 6),
        "installation_year": installation_year,
        "age_years": age_years,
        "capacity_mva": capacity_mva,
        "customers_served": customers_served,
        "critical_facility_count": critical_facility_count,
        "historical_failures": hist_fail,
        "current_health_score": current_health_score,
    }
    assets_list.append(asset)

assets_df = pd.DataFrame(assets_list)

# Quick sanity: print a couple of high-risk vs low-risk examples
worst = assets_df.loc[assets_df["current_health_score"].idxmin()]
best = assets_df.loc[assets_df["current_health_score"].idxmax()]
print(f"  -> Low-health example: {worst.asset_id} score={worst.current_health_score} "
      f"age={worst.age_years}yr failures={worst.historical_failures}")
print(f"  -> High-health example: {best.asset_id} score={best.current_health_score} "
      f"age={best.age_years}yr failures={best.historical_failures}")


# ============================================================
# 2. GENERATE SENSOR READINGS (time-series)
# ============================================================
print("[2/5] Generating sensor_readings.csv ...")

readings_list = []
start_time = datetime(2026, 9, 1, 0, 0, 0)

for asset_idx, asset in enumerate(assets_list):
    aid = asset["asset_id"]
    health = asset["current_health_score"]
    age = asset["age_years"]
    capacity = asset["capacity_mva"]

    # Build an asset-level anomaly factor.
    # Low health -> high anomaly probability & magnitude
    anomaly_base = clip((100 - health) / 100.0, 0.0, 1.0)  # 0..1
    # Make some healthy assets have random transient spikes too (realistic)
    extra_spike_prob = 0.04 if health > 70 else 0.0

    base_temperature = 35 + (age * 0.25) + anomaly_base * 22
    base_vibration   = 0.02 + (age * 0.0012) + anomaly_base * 0.18
    base_pd          = 5 + anomaly_base * 90                  # partial discharge (pC)
    base_oil         = 92 - anomaly_base * 48                 # oil quality %
    base_load        = 40 + np.random.uniform(-5, 15) + anomaly_base * 20
    base_voltage     = 13200 if capacity >= 40 else 4160

    reading_times = [start_time + timedelta(hours=h, minutes=np.random.randint(0, 59))
                     for h in range(NUM_READINGS_PER_ASSET)]

    for t in reading_times:
        # Daily cycle: load peaks at midday & early evening
        hour = t.hour
        daily_factor = 1.0 + 0.18 * np.sin((hour - 6) * np.pi / 12)  # peak 12-18

        # Random variation
        noise_load = np.random.normal(0, 4.5)

        is_anomaly_hour = (np.random.rand() < (anomaly_base * 0.30 + extra_spike_prob))

        if is_anomaly_hour:
            spike_mult = np.random.uniform(1.25, 2.4)
        else:
            spike_mult = 1.0

        # Load
        load_pct = clip(base_load * daily_factor + noise_load, 5, 115) * spike_mult
        load_pct = clip(load_pct, 2, 120)

        # Temperature: rises with load & health
        temp_noise = np.random.normal(0, 2.0)
        temperature = (base_temperature
                       + (load_pct - 50) * 0.18
                       + temp_noise) * (1.0 + (spike_mult - 1) * 1.3)
        temperature = clip(temperature, 15, 140)

        # Vibration: rises with load and anomaly state
        vib_noise = np.random.normal(0, 0.005)
        vibration = (base_vibration
                     + (load_pct - 50) * 0.0004
                     + vib_noise) * spike_mult
        vibration = clip(vibration, 0.005, 0.6)

        # Partial discharge: low-health + anomaly hour -> high
        pd_noise = np.random.normal(0, 4)
        partial_discharge = (base_pd + pd_noise) * spike_mult
        partial_discharge = clip(partial_discharge, 1, 350)

        # Oil quality: degrades with temperature & age
        oil_drop_temp = max(0, temperature - 60) * 0.4
        oil_noise = np.random.normal(0, 2.0)
        oil_quality = base_oil - oil_drop_temp + oil_noise
        oil_quality = clip(oil_quality, 10, 100)

        # Voltage: sags slightly under high load
        voltage_sag = 1.0 - (max(0, load_pct - 80) * 0.0008)
        voltage = base_voltage * voltage_sag + np.random.normal(0, base_voltage * 0.003)
        voltage = clip(voltage, base_voltage * 0.82, base_voltage * 1.08)

        # Current: scales with load / voltage (approx)
        current = ((load_pct / 100.0) * capacity * 1_000_000) / (voltage * np.sqrt(3))
        current = current * 0.001  # kA
        current += np.random.normal(0, current * 0.015)
        current = clip(current, 0.005, 15.0)

        # Derived health score (0-100) from sensor panel
        score_temp = 100 - clip((temperature - 30) * 1.3, 0, 85)
        score_vib  = 100 - clip((vibration - 0.02) * 420, 0, 85)
        score_pd   = 100 - clip((partial_discharge - 5) * 0.9, 0, 90)
        score_oil  = oil_quality
        score_load = 100 - clip(max(0, load_pct - 70) * 1.4, 0, 60)
        health_score = int(clip(np.mean(
            [score_temp, score_vib, score_pd, score_oil, score_load]
        ), 0, 100))

        readings_list.append({
            "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "asset_id": aid,
            "temperature": round(temperature, 2),
            "vibration": round(vibration, 4),
            "partial_discharge": round(partial_discharge, 2),
            "oil_quality": round(oil_quality, 2),
            "load_percentage": round(load_pct, 2),
            "voltage": round(voltage, 2),
            "current": round(current, 4),
            "health_score": health_score,
        })

readings_df = pd.DataFrame(readings_list)
print(f"  -> Generated {len(readings_df):,} sensor readings")


# ============================================================
# 3. GENERATE INCIDENTS (historical outages & failures)
# ============================================================
print("[3/5] Generating incidents.csv ...")

# Weight each asset by failure risk
risk_scores = []
for _, a in assets_df.iterrows():
    risk = (
        a["historical_failures"] * 2.2
        + max(0, a["age_years"] - 15) * 0.6
        + max(0, 85 - a["current_health_score"]) * 0.55
        + a["critical_facility_count"] * 0.25
        + 0.3
    )
    risk_scores.append(risk)
risk_scores = np.array(risk_scores)
risk_probs = risk_scores / risk_scores.sum()

incidents_list = []
incident_start = datetime(2023, 1, 1)
incident_end = datetime(2026, 9, 1)
total_hours = int((incident_end - incident_start).total_seconds() // 3600)

for j in range(1, NUM_INCIDENTS + 1):
    asset_row = assets_df.sample(n=1, weights=risk_probs, random_state=SEED + j).iloc[0]
    aid = asset_row["asset_id"]

    incident_type = np.random.choice(INCIDENT_TYPES)

    # Severity influenced by asset characteristics
    sev_weights = np.array(SEVERITY_WEIGHTS, dtype=float)
    sev_weights[0] *= clip(1.0 - asset_row["age_years"] / 60.0, 0.2, 1.4)  # low sev less likely with age
    sev_weights[3] *= clip(0.5 + asset_row["historical_failures"] / 20.0, 0.5, 3.0)
    sev_weights = sev_weights / sev_weights.sum()
    severity = np.random.choice(SEVERITIES, p=sev_weights)

    sev_idx = SEVERITIES.index(severity)

    # Random time within range
    offset_h = np.random.randint(0, total_hours)
    incident_date = incident_start + timedelta(hours=offset_h,
                                               minutes=np.random.randint(0, 59))

    # Duration: higher severity -> longer
    base_dur = [2, 8, 24, 72][sev_idx]
    duration_hours = round(max(0.5, np.random.gamma(base_dur * 0.6, 1.6)), 1)

    # Customers affected: scales with asset customers and severity
    cust_factor = [0.05, 0.25, 0.65, 0.95][sev_idx]
    customers_affected = int(clip(
        asset_row["customers_served"] * cust_factor * np.random.uniform(0.6, 1.3),
        0, None
    ))

    # Repair cost: severity x duration x capacity
    sev_cost_mult = [400, 2500, 12000, 45000][sev_idx]
    repair_cost = round(
        sev_cost_mult
        * (0.5 + duration_hours / 10.0)
        * (0.6 + asset_row["capacity_mva"] / 60.0)
        * np.random.uniform(0.7, 1.3),
        2
    )

    # Weather related? Some incident types are naturally so
    weather_related = 0
    if incident_type in ("Lightning Strike", "Tree Contact", "Conductor Damage"):
        weather_related = np.random.choice([0, 1], p=[0.2, 0.8])
    elif severity in ("high", "critical") and np.random.rand() < 0.35:
        weather_related = 1
    elif np.random.rand() < 0.18:
        weather_related = 1

    # Actual failure occurred? Most incidents are "events", some are warnings
    failure_occurred = 1
    if severity == "low" and np.random.rand() < 0.55:
        failure_occurred = 0
    elif severity == "medium" and np.random.rand() < 0.20:
        failure_occurred = 0

    incidents_list.append({
        "incident_id": f"INC-{j:04d}",
        "asset_id": aid,
        "incident_date": incident_date.strftime("%Y-%m-%d %H:%M:%S"),
        "incident_type": incident_type,
        "severity": severity,
        "duration_hours": duration_hours,
        "customers_affected": customers_affected,
        "repair_cost": repair_cost,
        "weather_related": weather_related,
        "failure_occurred": failure_occurred,
    })

incidents_df = pd.DataFrame(incidents_list)
print(f"  -> Generated {len(incidents_df)} incidents "
      f"(critical={int((incidents_df.severity=='critical').sum())}, "
      f"weather-related={int(incidents_df.weather_related.sum())})")


# ============================================================
# 4. GENERATE WEATHER (multi-region, time-series)
# ============================================================
print("[4/5] Generating weather.csv ...")

weather_list = []
wx_start = datetime(2026, 9, 1, 0, 0, 0)
hours_per_region = NUM_WEATHER_RECORDS // len(REGIONS)

for region in REGIONS:
    for h in range(hours_per_region):
        ts = wx_start + timedelta(hours=h * 3)  # every 3 hours
        hour = ts.hour
        day_of_year = ts.timetuple().tm_yday

        # Seasonal cycle (Sept ~ day 244 in NH, summer->fall transition)
        season_temp_amp = 12 * np.cos((day_of_year - 200) * 2 * np.pi / 365)
        daily_temp_amp = 8 * np.sin((hour - 6) * np.pi / 12)
        base_temp = 20 + season_temp_amp + daily_temp_amp
        temperature = round(base_temp + np.random.normal(0, 1.5), 2)

        # Humidity: higher near rivers, cooler hours
        humidity_base = 62 + (1 if "Riverside" in region["name"] else 0) * 8
        humidity = clip(humidity_base - (temperature - 20) * 0.7 + np.random.normal(0, 7),
                        15, 100)

        # Is this a storm window? Generate some severe days.
        region_storm_prob = 0.08
        if "Eastside" in region["name"] or "Riverside" in region["name"]:
            region_storm_prob = 0.12
        is_stormy = np.random.rand() < region_storm_prob

        if is_stormy:
            wind_speed = round(np.random.uniform(25, 65), 2)
            rainfall = round(np.random.exponential(8) + np.random.uniform(0, 3), 2)
        else:
            wind_speed = round(clip(np.random.gamma(2.4, 3.2), 0.2, None), 2)
            rainfall = round(0.0 if np.random.rand() > 0.22 else np.random.exponential(1.2), 2)

        # Severe weather flag
        severe = 0
        if (wind_speed >= 40) or (rainfall >= 15) or (humidity >= 92 and temperature <= 0):
            severe = 1
        if is_stormy and (wind_speed > 50 or rainfall > 20):
            severe = 1

        # Storm risk index 0-100, composite
        wind_risk = clip(wind_speed * 1.2, 0, 60)
        rain_risk = clip(rainfall * 3.5, 0, 60)
        humidity_risk = clip((humidity - 70) * 0.8, 0, 20)
        storm_risk = int(clip(wind_risk + rain_risk + humidity_risk + severe * 15, 0, 100))

        weather_list.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "region": region["name"],
            "latitude": region["lat"],
            "longitude": region["lon"],
            "temperature": temperature,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "humidity": round(humidity, 2),
            "storm_risk": storm_risk,
            "severe_weather": severe,
        })

weather_df = pd.DataFrame(weather_list)
print(f"  -> Generated {len(weather_df)} weather records "
      f"(severe={int(weather_df.severe_weather.sum())}, "
      f"avg storm_risk={weather_df.storm_risk.mean():.1f})")


# ============================================================
# 5. GENERATE CREWS
# ============================================================
print("[5/5] Generating crews.csv ...")

CREW_NAMES = [
    ("Alpha Team",   "Transformer & Substation"),
    ("Bravo Team",   "Transmission Line"),
    ("Charlie Team", "Emergency Storm Response"),
    ("Delta Team",   "Switchgear & Protection"),
    ("Echo Team",    "Underground Cable"),
    ("Foxtrot Team", "Generator & Battery"),
    ("Golf Team",    "Inspection & Diagnostics"),
]

crews_list = []
for k in range(min(NUM_CREWS, len(CREW_NAMES))):
    region = REGIONS[np.random.randint(0, len(REGIONS))]
    crews_list.append({
        "crew_id": f"CRW-{k+1:03d}",
        "crew_name": CREW_NAMES[k][0],
        "latitude": round(region["lat"] + np.random.uniform(-0.015, 0.015), 6),
        "longitude": round(region["lon"] + np.random.uniform(-0.015, 0.015), 6),
        "specialization": CREW_NAMES[k][1],
        "availability": np.random.choice(["available", "standby", "dispatched", "on_leave"],
                                         p=[0.45, 0.20, 0.25, 0.10]),
    })

crews_df = pd.DataFrame(crews_list)
print(f"  -> Generated {len(crews_df)} crews")


# ============================================================
# WRITE ALL CSVs
# ============================================================
DEMO_BANNER = (
    "# ============================================================\n"
    "# GridGuard AI - DEMONSTRATION DATA (SYNTHETIC)\n"
    "# THIS FILE CONTAINS ARTIFICIALLY GENERATED DATA FOR\n"
    "# PROTOTYPING, EDUCATION AND HACKATHON USE ONLY.\n"
    "# NOT REAL UTILITY OPERATIONAL DATA.\n"
    "# Generated: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + "\n"
    "# ============================================================\n"
)


def write_csv_with_banner(df, filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="") as f:
        f.write(DEMO_BANNER)
    df.to_csv(path, mode="a", index=False)
    print(f"  wrote: {path}  ({len(df)} rows)")


write_csv_with_banner(assets_df,       "assets.csv")
write_csv_with_banner(readings_df,     "sensor_readings.csv")
write_csv_with_banner(incidents_df,    "incidents.csv")
write_csv_with_banner(weather_df,      "weather.csv")
write_csv_with_banner(crews_df,        "crews.csv")


# ============================================================
# QUICK VALIDATION
# ============================================================
print("\n--- VALIDATION CHECKS ---")

# Correlation: age vs health_score (should be negative)
corr_age_health = assets_df["age_years"].corr(assets_df["current_health_score"])
print(f"  Corr(age, health_score)      = {corr_age_health:+.3f}  (expected negative, stronger = better)")

# Corr: historical_failures vs health (negative)
corr_fail_health = assets_df["historical_failures"].corr(assets_df["current_health_score"])
print(f"  Corr(failures, health_score) = {corr_fail_health:+.3f}  (expected negative)")

# Avg sensor health: group by asset, compare with asset.current_health_score
avg_sensor = readings_df.groupby("asset_id")["health_score"].mean().rename("avg_sensor_health")
chk = assets_df.set_index("asset_id").join(avg_sensor)
corr_sensor_asset = chk["current_health_score"].corr(chk["avg_sensor_health"])
print(f"  Corr(asset_health, sensor_avg_health) = {corr_sensor_asset:+.3f}  (expected positive)")

# Avg sensor temp vs load_pct
corr_temp_load = readings_df["temperature"].corr(readings_df["load_percentage"])
print(f"  Corr(temperature, load_pct)  = {corr_temp_load:+.3f}  (expected positive)")

# Severe weather -> higher storm_risk
mean_sr_severe = weather_df.loc[weather_df.severe_weather == 1, "storm_risk"].mean()
mean_sr_normal = weather_df.loc[weather_df.severe_weather == 0, "storm_risk"].mean()
print(f"  Avg storm_risk: severe={mean_sr_severe:.1f} vs normal={mean_sr_normal:.1f}  (severe >> normal)")

# Incidents: severity vs repair_cost
sev_cost = incidents_df.groupby("severity")["repair_cost"].mean().reindex(SEVERITIES)
print(f"  Avg repair_cost by severity: " +
      ", ".join([f"{s}={sev_cost[s]:,.0f}" for s in SEVERITIES]))

print("\nDone! All demonstration datasets generated successfully.")
print("All files are clearly marked as DEMONSTRATION / SYNTHETIC data.")
