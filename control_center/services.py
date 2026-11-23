"""
Business logic and analytics services for Drones RBG.
Handles flight telemetry generation, real-time interpolation, and fleet audit calculations.
"""

import math
import random
from datetime import datetime, timezone, timedelta
from .db_client import get_db, serialize_doc, register_telemetry_reading


def get_fleet_summary():
    """Returns aggregated fleet health and mission statistics."""
    db = get_db()
    drones = list(db.drones.find({}))
    missions = list(db.missions.find({}))
    telemetry_count = db.telemetry.count_documents({})

    available_drones = sum(1 for d in drones if d.get('status') == 'AVAILABLE')
    in_mission_drones = sum(1 for d in drones if d.get('status') == 'IN_MISSION')
    maintenance_drones = sum(1 for d in drones if d.get('status') == 'MAINTENANCE')

    total_flight_hours = sum(d.get('total_flight_hours', 0.0) for d in drones)
    completed_missions = sum(1 for m in missions if m.get('status') == 'COMPLETED')
    active_missions = sum(1 for m in missions if m.get('status') == 'IN_PROGRESS')

    avg_battery = round(sum(d.get('battery_level', 0) for d in drones) / max(len(drones), 1), 1)

    return {
        "total_drones": len(drones),
        "available_drones": available_drones,
        "in_mission_drones": in_mission_drones,
        "maintenance_drones": maintenance_drones,
        "total_flight_hours": round(total_flight_hours, 1),
        "total_missions": len(missions),
        "completed_missions": completed_missions,
        "active_missions": active_missions,
        "telemetry_count": telemetry_count,
        "avg_battery": avg_battery,
        "drones": serialize_doc(drones),
        "recent_missions": serialize_doc(missions[:5])
    }


def get_mission_audit_analytics(mission_id):
    """
    Computes time-series telemetry metrics for a mission:
    - Battery consumption vs flight conditions (speed, altitude, wind)
    - Altitude profile
    - Energy efficiency (Wh/km, %/km)
    - Diagnostic anomalies
    """
    db = get_db()
    mission = db.missions.find_one({"mission_id": mission_id})
    if not mission:
        return None

    # Fetch time-series telemetry ordered by timestamp
    telemetry_cursor = db.telemetry.find({"mission_id": mission_id}).sort("timestamp", 1)
    telemetry_list = list(telemetry_cursor)

    if not telemetry_list:
        return {
            "mission": serialize_doc(mission),
            "telemetry_count": 0,
            "chart_data": {
                "timestamps": [],
                "battery": [],
                "speed": [],
                "altitude": [],
                "motor_temp": [],
                "power_w": []
            },
            "summary_metrics": {
                "avg_speed_kmh": 0,
                "max_speed_kmh": 0,
                "max_altitude_m": 0,
                "avg_altitude_m": 0,
                "total_duration_sec": 0,
                "battery_drop_pct": 0,
                "efficiency_pct_per_km": 0,
                "avg_motor_temp_c": 0
            }
        }

    timestamps = []
    battery_series = []
    speed_series = []
    altitude_series = []
    motor_temp_series = []
    power_w_series = []

    speeds = []
    altitudes = []
    motor_temps = []

    for idx, t in enumerate(telemetry_list):
        ts = t.get("timestamp")
        if isinstance(ts, datetime):
            label = ts.strftime("%H:%M:%S")
        else:
            label = f"+{t.get('elapsed_seconds', idx*15)}s"
        timestamps.append(label)

        batt = t.get("power", {}).get("battery_pct", 100)
        battery_series.append(batt)

        spd = t.get("flight_dynamics", {}).get("speed_kmh", 0)
        speed_series.append(spd)
        speeds.append(spd)

        alt = t.get("gps", {}).get("altitude_m", 0)
        altitude_series.append(alt)
        altitudes.append(alt)

        m_temp = t.get("diagnostics", {}).get("motor_temp_c", 30)
        motor_temp_series.append(m_temp)
        motor_temps.append(m_temp)

        pw = t.get("power", {}).get("power_w", 200)
        power_w_series.append(pw)

    initial_batt = battery_series[0] if battery_series else 100
    final_batt = battery_series[-1] if battery_series else initial_batt
    battery_drop = round(max(0, initial_batt - final_batt), 1)

    dist_km = mission.get("total_distance_m", 1500) / 1000.0
    efficiency = round(battery_drop / max(dist_km, 0.1), 2)

    avg_speed = round(sum(speeds) / max(len(speeds), 1), 1)
    max_speed = round(max(speeds) if speeds else 0, 1)
    avg_alt = round(sum(altitudes) / max(len(altitudes), 1), 1)
    max_alt = round(max(altitudes) if altitudes else 0, 1)
    avg_temp = round(sum(motor_temps) / max(len(motor_temps), 1), 1)

    return {
        "mission": serialize_doc(mission),
        "telemetry_count": len(telemetry_list),
        "chart_data": {
            "timestamps": timestamps,
            "battery": battery_series,
            "speed": speed_series,
            "altitude": altitude_series,
            "motor_temp": motor_temp_series,
            "power_w": power_w_series
        },
        "summary_metrics": {
            "avg_speed_kmh": avg_speed,
            "max_speed_kmh": max_speed,
            "max_altitude_m": max_alt,
            "avg_altitude_m": avg_alt,
            "total_duration_sec": len(telemetry_list) * 15,
            "battery_drop_pct": battery_drop,
            "efficiency_pct_per_km": efficiency,
            "avg_motor_temp_c": avg_temp,
            "total_distance_m": mission.get("total_distance_m", 0)
        },
        "raw_telemetry_sample": serialize_doc(telemetry_list[:10])
    }


def simulate_live_telemetry_tick(mission_id, progress_step=None):
    """
    Simulates one real-time telemetry burst packet along the mission waypoints,
    persisting it into MongoDB using PyMongo insert_one.
    """
    db = get_db()
    mission = db.missions.find_one({"mission_id": mission_id})
    if not mission:
        return {"error": "Mission not found"}

    waypoints = mission.get("waypoints", [])
    if not waypoints:
        return {"error": "Mission has no waypoints"}

    # Count existing telemetry points to determine current tick
    existing_count = db.telemetry.count_documents({"mission_id": mission_id})
    tick = progress_step if progress_step is not None else existing_count

    total_ticks = max(len(waypoints) * 8, 30)
    fraction = min(1.0, tick / float(total_ticks))

    # Calculate waypoint segment
    num_segments = len(waypoints) - 1
    if num_segments <= 0:
        target_wp = waypoints[0]
        cur_lat = target_wp["lat"]
        cur_lng = target_wp["lng"]
        cur_alt = target_wp.get("alt", 30.0)
        cur_action = target_wp.get("action", "CRUISE")
    else:
        seg_float = fraction * num_segments
        seg_idx = min(int(seg_float), num_segments - 1)
        sub_frac = seg_float - seg_idx
        
        wp_a = waypoints[seg_idx]
        wp_b = waypoints[seg_idx + 1]

        cur_lat = wp_a["lat"] + (wp_b["lat"] - wp_a["lat"]) * sub_frac
        cur_lng = wp_a["lng"] + (wp_b["lng"] - wp_a["lng"]) * sub_frac
        cur_alt = wp_a.get("alt", 30) + (wp_b.get("alt", 30) - wp_a.get("alt", 30)) * sub_frac
        cur_action = wp_b.get("action", "FLYING_TO_WP")

    # Dynamic variables
    drone_id = mission.get("assigned_drone_id", "DRN-RBG-01")
    drone = db.drones.find_one({"drone_id": drone_id}) or {}
    start_batt = drone.get("battery_level", 95.0)

    # Battery decreases smoothly
    battery_current = max(10.0, start_batt - (fraction * 28.0))
    speed_ms = 8.5 + random.uniform(-1.0, 1.5) if (fraction > 0.05 and fraction < 0.95) else 2.5
    motor_temp = 32.0 + (fraction * 16.0) + random.uniform(-0.5, 0.5)

    now = datetime.now(timezone.utc)
    packet = {
        "mission_id": mission_id,
        "drone_id": drone_id,
        "timestamp": now,
        "elapsed_seconds": tick * 5,
        "current_action": cur_action,
        "fraction_complete": round(fraction * 100, 1),
        "gps": {
            "lat": round(cur_lat, 6),
            "lng": round(cur_lng, 6),
            "altitude_m": round(cur_alt, 1),
            "relative_alt_m": round(cur_alt, 1),
            "satellites": 19
        },
        "flight_dynamics": {
            "speed_ms": round(speed_ms, 1),
            "speed_kmh": round(speed_ms * 3.6, 1),
            "vertical_speed_ms": round(random.uniform(-0.4, 0.4), 1),
            "pitch_deg": round(math.sin(tick * 0.4) * 5.0, 1),
            "roll_deg": round(math.cos(tick * 0.3) * 4.0, 1),
            "yaw_deg": round((tick * 15.0) % 360, 1)
        },
        "power": {
            "battery_pct": round(battery_current, 1),
            "voltage_v": round(21.4 - (fraction * 2.2), 2),
            "current_a": round(15.2 + (speed_ms * 0.6), 1),
            "power_w": round((15.2 + speed_ms * 0.6) * 21.0, 1),
            "est_remaining_min": round((battery_current / 100.0) * 45.0, 1)
        },
        "diagnostics": {
            "motor_temp_c": round(motor_temp, 1),
            "esc_temp_c": round(motor_temp - 3.5, 1),
            "signal_rssi_dbm": random.randint(-64, -58),
            "wind_speed_kmh": round(10.2 + random.uniform(-2, 2), 1),
            "sensor_health": "NORMAL",
            "cpu_load_pct": random.randint(30, 48)
        }
    }

    # Registrar telemetría usando la función de backend con operador $push en telemetria_misiones
    register_telemetry_reading(mission_id, packet)

    # Update drone's current battery and position
    db.drones.update_one(
        {"drone_id": drone_id},
        {"$set": {
            "battery_level": round(battery_current, 1),
            "status": "COMPLETED" if fraction >= 1.0 else "IN_MISSION",
            "last_telemetry_at": now
        }}
    )

    # Update mission status if completed
    if fraction >= 1.0:
        db.missions.update_one(
            {"mission_id": mission_id},
            {"$set": {
                "status": "COMPLETED",
                "completed_at": now,
                "battery_consumed_pct": round(start_batt - battery_current, 1)
            }}
        )
    elif mission.get("status") == "PLANNED":
        db.missions.update_one(
            {"mission_id": mission_id},
            {"$set": {
                "status": "IN_PROGRESS",
                "started_at": now
            }}
        )

    return serialize_doc(packet)


# ==============================================================================
# Consultas de Agregación Nativas de MongoDB (Aggregation Pipeline)
# Requisito Rúbrica Semana 6 & Hito Final (10 puntos)
# ==============================================================================

def get_sector_analytics_aggregation():
    """
    Agregación Nativa 1: Rendimiento y Desempeño Operativo por Sector.
    Pregunta de negocio: ¿Cuál es el volumen de misiones, distancia promedio recorrida,
    consumo medio de batería y aeronaves utilizadas por sector (Industrial, Agrícola, Seguridad)?
    Pipeline stages: $group -> $project -> $sort
    """
    db = get_db()
    pipeline = [
        {
            "$group": {
                "_id": "$sector",
                "total_missions": {"$sum": 1},
                "completed_missions": {
                    "$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}
                },
                "in_progress_missions": {
                    "$sum": {"$cond": [{"$eq": ["$status", "IN_PROGRESS"]}, 1, 0]}
                },
                "planned_missions": {
                    "$sum": {"$cond": [{"$eq": ["$status", "PLANNED"]}, 1, 0]}
                },
                "avg_distance_m": {"$avg": "$total_distance_m"},
                "avg_battery_consumed_pct": {"$avg": "$battery_consumed_pct"},
                "avg_duration_min": {"$avg": "$estimated_duration_min"},
                "max_distance_m": {"$max": "$total_distance_m"},
                "drones_used": {"$addToSet": "$drone_name"}
            }
        },
        {
            "$project": {
                "sector": "$_id",
                "_id": 0,
                "total_missions": 1,
                "completed_missions": 1,
                "in_progress_missions": 1,
                "planned_missions": 1,
                "avg_distance_m": {"$round": ["$avg_distance_m", 1]},
                "avg_battery_consumed_pct": {"$round": ["$avg_battery_consumed_pct", 1]},
                "avg_duration_min": {"$round": ["$avg_duration_min", 1]},
                "max_distance_m": {"$round": ["$max_distance_m", 1]},
                "drones_used": 1,
                "unique_drones_count": {"$size": "$drones_used"}
            }
        },
        {"$sort": {"total_missions": -1}}
    ]

    try:
        results = list(db.missions.aggregate(pipeline))
        return serialize_doc(results)
    except Exception as exc:
        print(f">>> [Aggregation 1 Error] {exc}")
        return []


def get_waypoint_tasks_aggregation():
    """
    Agregación Nativa 2: Demanda y Métricas por Tipo de Tarea en Waypoints.
    Pregunta de negocio: ¿Cuáles son las tareas/sensores más demandados en los planes de vuelo
    (RGB, FLIR, NDVI, LiDAR), cuántas ejecuciones acumulan y a qué altitud/velocidad promedio operan?
    Pipeline stages: $unwind (arreglo embebido waypoints) -> $group -> $project -> $sort
    """
    db = get_db()
    pipeline = [
        {"$unwind": "$waypoints"},
        {
            "$group": {
                "_id": "$waypoints.action",
                "total_executions": {"$sum": 1},
                "avg_altitude_m": {"$avg": "$waypoints.alt"},
                "avg_speed_ms": {"$avg": "$waypoints.speed_ms"},
                "min_altitude_m": {"$min": "$waypoints.alt"},
                "max_altitude_m": {"$max": "$waypoints.alt"}
            }
        },
        {
            "$project": {
                "task_action": "$_id",
                "_id": 0,
                "total_executions": 1,
                "avg_altitude_m": {"$round": ["$avg_altitude_m", 1]},
                "avg_speed_ms": {"$round": ["$avg_speed_ms", 1]},
                "avg_speed_kmh": {"$round": [{"$multiply": ["$avg_speed_ms", 3.6]}, 1]},
                "min_altitude_m": 1,
                "max_altitude_m": 1
            }
        },
        {"$sort": {"total_executions": -1}}
    ]

    try:
        results = list(db.missions.aggregate(pipeline))
        return serialize_doc(results)
    except Exception as exc:
        print(f">>> [Aggregation 2 Error] {exc}")
        return []

