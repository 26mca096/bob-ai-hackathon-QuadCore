import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.models import (
    db, Asset, SensorReading, Incident, Weather, Crew,
    Prediction, MaintenanceRecommendation
)


def safe_float(val):
    try:
        if pd.isna(val) or str(val).strip() == '':
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    try:
        if pd.isna(val) or str(val).strip() == '':
            return None
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_date(val):
    try:
        if pd.isna(val) or str(val).strip() == '':
            return None
        dt = pd.to_datetime(val)
        return dt.date()
    except (ValueError, TypeError):
        return None


def safe_datetime(val):
    try:
        if pd.isna(val) or str(val).strip() == '':
            return None
        return pd.to_datetime(val).to_pydatetime()
    except (ValueError, TypeError):
        return None


def safe_str(val):
    try:
        if pd.isna(val):
            return None
        s = str(val).strip()
        return s if s else None
    except (ValueError, TypeError):
        return None


def read_csv_skip_banner(csv_path):
    """Read CSV, skipping any leading comment lines that start with '#'."""
    skip_rows = 0
    with open(csv_path, 'r') as f:
        for line in f:
            if line.strip().startswith('#') or line.strip() == '':
                skip_rows += 1
            else:
                break
    return pd.read_csv(csv_path, skiprows=skip_rows)


def import_assets(app):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'assets.csv')
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found, skipping assets import")
        return 0, 0

    try:
        df = read_csv_skip_banner(csv_path)
    except Exception as e:
        print(f"ERROR reading assets.csv: {e}")
        return 0, 0

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                asset_id = safe_str(row.get('asset_id'))
                if not asset_id:
                    skipped += 1
                    continue

                existing = Asset.query.filter_by(asset_id=asset_id).first()
                if existing:
                    skipped += 1
                    continue

                asset = Asset(
                    asset_id=asset_id,
                    asset_type=safe_str(row.get('asset_type')),
                    substation_id=safe_str(row.get('substation_id')),
                    location=safe_str(row.get('location')),
                    latitude=safe_float(row.get('latitude')),
                    longitude=safe_float(row.get('longitude')),
                    installation_year=safe_int(row.get('installation_year')),
                    age_years=safe_int(row.get('age_years')),
                    capacity_mva=safe_float(row.get('capacity_mva')),
                    customers_served=safe_int(row.get('customers_served')),
                    critical_facility_count=safe_int(row.get('critical_facility_count')),
                    historical_failures=safe_int(row.get('historical_failures')),
                    current_health_score=safe_int(row.get('current_health_score')),
                    name=safe_str(row.get('asset_type')) and f"{safe_str(row.get('asset_type'))} {asset_id}",
                    type=safe_str(row.get('asset_type')),
                    install_date=safe_str(row.get('installation_year')) and safe_date(f"{int(float(row.get('installation_year', 2020)))}-06-30"),
                    status='operational'
                )
                if asset.current_health_score is not None:
                    if asset.current_health_score < 30:
                        asset.status = 'critical'
                    elif asset.current_health_score < 55:
                        asset.status = 'degraded'
                    elif asset.current_health_score < 75:
                        asset.status = 'maintenance'
                    else:
                        asset.status = 'operational'

                db.session.add(asset)
                imported += 1
            except Exception as e:
                print(f"  ERROR importing asset row {idx}: {e}")
                skipped += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR committing assets: {e}")
            return 0, imported + skipped

    return imported, skipped


def import_sensor_readings(app):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'sensor_readings.csv')
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found, skipping sensor_readings import")
        return 0, 0

    try:
        df = read_csv_skip_banner(csv_path)
    except Exception as e:
        print(f"ERROR reading sensor_readings.csv: {e}")
        return 0, 0

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                asset_id = safe_str(row.get('asset_id'))
                ts = safe_datetime(row.get('timestamp'))
                if not asset_id or not ts:
                    skipped += 1
                    continue

                reading_id = f"SR-{asset_id}-{ts.strftime('%Y%m%d%H%M%S')}"

                existing = SensorReading.query.filter_by(reading_id=reading_id).first()
                if existing:
                    skipped += 1
                    continue

                reading = SensorReading(
                    reading_id=reading_id,
                    asset_id=asset_id,
                    timestamp=ts,
                    temperature=safe_float(row.get('temperature')),
                    vibration=safe_float(row.get('vibration')),
                    partial_discharge=safe_float(row.get('partial_discharge')),
                    oil_quality=safe_float(row.get('oil_quality')),
                    load_percentage=safe_float(row.get('load_percentage')),
                    voltage=safe_float(row.get('voltage')),
                    current=safe_float(row.get('current')),
                    health_score=safe_int(row.get('health_score')),
                    power=safe_float(row.get('power')),
                    humidity=safe_float(row.get('humidity'))
                )
                db.session.add(reading)
                imported += 1

                if imported % 500 == 0:
                    db.session.commit()
            except Exception as e:
                print(f"  ERROR importing sensor_reading row {idx}: {e}")
                skipped += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR committing sensor_readings: {e}")
            return imported - (imported % 500), skipped + (imported % 500)

    return imported, skipped


def import_incidents(app):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'incidents.csv')
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found, skipping incidents import")
        return 0, 0

    try:
        df = read_csv_skip_banner(csv_path)
    except Exception as e:
        print(f"ERROR reading incidents.csv: {e}")
        return 0, 0

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                incident_id = safe_str(row.get('incident_id'))
                if not incident_id:
                    skipped += 1
                    continue

                existing = Incident.query.filter_by(incident_id=incident_id).first()
                if existing:
                    skipped += 1
                    continue

                severity = safe_str(row.get('severity'))
                failure_occurred = safe_int(row.get('failure_occurred')) or 0
                weather_related = safe_int(row.get('weather_related')) or 0
                incident_dt = safe_datetime(row.get('incident_date'))
                duration = safe_float(row.get('duration_hours')) or 0.0
                resolved_dt = None
                if incident_dt and duration > 0:
                    resolved_dt = incident_dt + pd.Timedelta(hours=duration)

                status_map = {
                    0: 'resolved', 1: 'reported'
                }
                if failure_occurred == 1 and severity in ('high', 'critical'):
                    status = 'open'
                elif failure_occurred == 1:
                    status = 'in_progress'
                else:
                    status = 'resolved'

                incident = Incident(
                    incident_id=incident_id,
                    asset_id=safe_str(row.get('asset_id')),
                    incident_date=incident_dt,
                    incident_type=safe_str(row.get('incident_type')),
                    severity=severity,
                    duration_hours=safe_float(row.get('duration_hours')),
                    customers_affected=safe_int(row.get('customers_affected')),
                    repair_cost=safe_float(row.get('repair_cost')),
                    weather_related=weather_related,
                    failure_occurred=failure_occurred,
                    type=safe_str(row.get('incident_type')),
                    description=(f"{safe_str(row.get('incident_type')) or 'Incident'} "
                                 f"- severity {severity or 'unknown'}"),
                    reported_at=incident_dt,
                    resolved_at=resolved_dt,
                    status=status
                )
                db.session.add(incident)
                imported += 1
            except Exception as e:
                print(f"  ERROR importing incident row {idx}: {e}")
                skipped += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR committing incidents: {e}")
            return 0, imported + skipped

    return imported, skipped


def import_weather(app):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'weather.csv')
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found, skipping weather import")
        return 0, 0

    try:
        df = read_csv_skip_banner(csv_path)
    except Exception as e:
        print(f"ERROR reading weather.csv: {e}")
        return 0, 0

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                region = safe_str(row.get('region'))
                ts = safe_datetime(row.get('timestamp'))
                if not region or not ts:
                    skipped += 1
                    continue

                weather_id = f"WX-{region.replace(' ', '_')}-{ts.strftime('%Y%m%d%H%M%S')}"

                existing = Weather.query.filter_by(weather_id=weather_id).first()
                if existing:
                    skipped += 1
                    continue

                severe = safe_int(row.get('severe_weather')) or 0
                rainfall = safe_float(row.get('rainfall')) or 0.0
                cond = 'Sunny'
                if rainfall > 10:
                    cond = 'Heavy Rain'
                elif rainfall > 0:
                    cond = 'Light Rain'
                if severe == 1:
                    cond = f"Severe - {cond}"

                weather = Weather(
                    weather_id=weather_id,
                    timestamp=ts,
                    region=region,
                    latitude=safe_float(row.get('latitude')),
                    longitude=safe_float(row.get('longitude')),
                    temperature=safe_float(row.get('temperature')),
                    rainfall=rainfall,
                    wind_speed=safe_float(row.get('wind_speed')),
                    humidity=safe_float(row.get('humidity')),
                    storm_risk=safe_int(row.get('storm_risk')),
                    severe_weather=severe,
                    location=region,
                    wind_direction='VAR',
                    precipitation=rainfall,
                    condition=cond
                )
                db.session.add(weather)
                imported += 1
            except Exception as e:
                print(f"  ERROR importing weather row {idx}: {e}")
                skipped += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR committing weather: {e}")
            return 0, imported + skipped

    return imported, skipped


def import_crews(app):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'crews.csv')
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found, skipping crews import")
        return 0, 0

    try:
        df = read_csv_skip_banner(csv_path)
    except Exception as e:
        print(f"ERROR reading crews.csv: {e}")
        return 0, 0

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                crew_id = safe_str(row.get('crew_id'))
                if not crew_id:
                    skipped += 1
                    continue

                existing = Crew.query.filter_by(crew_id=crew_id).first()
                if existing:
                    skipped += 1
                    continue

                crew_name = safe_str(row.get('crew_name'))
                availability = safe_str(row.get('availability')) or 'available'

                crew = Crew(
                    crew_id=crew_id,
                    crew_name=crew_name,
                    latitude=safe_float(row.get('latitude')),
                    longitude=safe_float(row.get('longitude')),
                    specialization=safe_str(row.get('specialization')),
                    availability=availability,
                    name=crew_name,
                    team_size=int(safe_int(row.get('team_size')) or (4 if 'Emergency' in str(crew_name or '') else 3)),
                    status=availability if availability in ('available', 'standby', 'dispatched', 'on_leave') else 'available',
                    current_location='Central Depot' if availability == 'available' else 'Field',
                    contact=f"555-{1000 + idx + 1:04d}"
                )
                db.session.add(crew)
                imported += 1
            except Exception as e:
                print(f"  ERROR importing crew row {idx}: {e}")
                skipped += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR committing crews: {e}")
            return 0, imported + skipped

    return imported, skipped


def main():
    print("=" * 60)
    print("GridGuard AI - Database Initialization & Import Script")
    print("=" * 60)

    app = create_app()

    print("\n[1/5] Importing Assets...")
    a_i, a_s = import_assets(app)
    print(f"  Imported: {a_i}, Skipped (duplicates/invalid): {a_s}")

    print("\n[2/5] Importing Sensor Readings...")
    sr_i, sr_s = import_sensor_readings(app)
    print(f"  Imported: {sr_i}, Skipped (duplicates/invalid): {sr_s}")

    print("\n[3/5] Importing Incidents...")
    i_i, i_s = import_incidents(app)
    print(f"  Imported: {i_i}, Skipped (duplicates/invalid): {i_s}")

    print("\n[4/5] Importing Weather Data...")
    w_i, w_s = import_weather(app)
    print(f"  Imported: {w_i}, Skipped (duplicates/invalid): {w_s}")

    print("\n[5/5] Importing Crews...")
    c_i, c_s = import_crews(app)
    print(f"  Imported: {c_i}, Skipped (duplicates/invalid): {c_s}")

    print("\n" + "=" * 60)
    total_i = a_i + sr_i + i_i + w_i + c_i
    total_s = a_s + sr_s + i_s + w_s + c_s
    print(f"TOTAL: Imported {total_i} records, Skipped {total_s} records")
    print("=" * 60)
    print("Done! Database is ready.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
