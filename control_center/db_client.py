"""
MongoDB PyMongo Client for Drones RBG Control Center.
Handles MongoDB connections via PyMongo driver with automatic fallback to mongomock
to guarantee seamless operation in both live MongoDB deployments and offline academic demos.
"""

import os
import math
import random
from datetime import datetime, timedelta, timezone
from django.conf import settings
from dotenv import load_dotenv
import pymongo
from bson import ObjectId

# Asegurar carga de variables de entorno desde archivo .env
load_dotenv()

try:
    import mongomock
    HAS_MONGOMOCK = True
except ImportError:
    HAS_MONGOMOCK = False

_client_instance = None
_db_instance = None
_is_mock_active = False
_connection_error_message = None


def get_mongo_client():
    global _client_instance, _db_instance, _is_mock_active, _connection_error_message
    
    if _client_instance is not None:
        return _client_instance, _is_mock_active

    mongo_uri = os.getenv("MONGO_URI") or getattr(settings, 'MONGO_SETTINGS', {}).get(
        'URI', 'mongodb://localhost:27017/drones_rbg'
    )
    timeout_ms = getattr(settings, 'MONGO_SETTINGS', {}).get('TIMEOUT_MS', 8000)

    try:
        real_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
        # Ping the server to verify connectivity
        real_client.admin.command('ping')
        _client_instance = real_client
        _is_mock_active = False
        _connection_error_message = None
        print(">>> [Drones RBG] Conectado exitosamente a MongoDB Nativo (PyMongo).")
        return _client_instance, False
    except Exception as exc:
        _connection_error_message = str(exc)
        print(f">>> [Drones RBG] No se pudo conectar a MongoDB en {mongo_uri} ({exc}).")
        if HAS_MONGOMOCK:
            print(">>> [Drones RBG] Activando motor PyMongo Mock in-memory para garantizar funcionamiento continuo.")
            _client_instance = mongomock.MongoClient()
            _is_mock_active = True
            return _client_instance, True
        else:
            raise RuntimeError(f"MongoDB no está disponible y mongomock no está instalado: {exc}")


def get_db():
    global _db_instance
    client, _ = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME") or getattr(settings, 'MONGO_SETTINGS', {}).get('DB_NAME', 'drones_rbg')
    _db_instance = client[db_name]
    return _db_instance


def get_db_status():
    _, is_mock = get_mongo_client()
    db = get_db()
    collections = db.list_collection_names()
    
    drones_count = db.drones.count_documents({})
    missions_count = db.missions.count_documents({})
    telemetry_count = db.telemetry.count_documents({})
    telemetria_misiones_count = db.telemetria_misiones.count_documents({})

    return {
        "is_mock": is_mock,
        "engine": "PyMongo Mock Engine (In-Memory)" if is_mock else "MongoDB Nativo (PyMongo Driver)",
        "status": "Simulado (In-Memory)" if is_mock else "Conectado (Servidor Activo)",
        "status_color": "warning" if is_mock else "success",
        "uri": os.getenv("MONGO_URI") or getattr(settings, 'MONGO_SETTINGS', {}).get('URI', 'mongodb://localhost:27017/drones_rbg'),
        "database": os.getenv("MONGO_DB_NAME") or getattr(settings, 'MONGO_SETTINGS', {}).get('DB_NAME', 'drones_rbg'),
        "collections": collections,
        "counts": {
            "drones": drones_count,
            "missions": missions_count,
            "telemetry": telemetry_count,
            "telemetria_misiones": telemetria_misiones_count
        },
        "last_error": _connection_error_message
    }


def serialize_doc(doc):
    """Recursively converts ObjectId and datetime to serializable primitives."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                result[k] = serialize_doc(v)
            else:
                result[k] = v
        return result
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def seed_database(force=False):
    """
    Populates MongoDB with rich industrial, agricultural and security drone data,
    demonstrating heterogeneous waypoints and time-series telemetry bursts.
    """
    db = get_db()

    if not force and db.drones.count_documents({}) > 0 and db.missions.count_documents({}) > 0:
        return False

    # Clear existing if forced
    if force:
        db.drones.delete_many({})
        db.missions.delete_many({})
        db.telemetry.delete_many({})
        db.telemetria_misiones.delete_many({})

    # 1. Drones Collection
    drones_data = [
        {
            "drone_id": "DRN-RBG-01",
            "name": "SkySentinel Alpha V",
            "model": "DJI Matrice 350 RTK Industrial",
            "status": "AVAILABLE",
            "battery_level": 94,
            "max_flight_time_min": 55,
            "max_speed_kmh": 82.8,
            "max_altitude_m": 7000,
            "payload_types": ["Cámara Zenmuse H20T (Térmica + Zoom 200x)", "Telémetro Láser (LIDAR)", "Foco Nocturno"],
            "operator_assigned": "Rodrigo Tapia",
            "total_flight_hours": 142.5,
            "firmware": "v04.01.0205",
            "health_status": "EXCELLENT",
            "home_base": {"name": "Base Central RBG Santiago", "lat": -33.4372, "lng": -70.6506, "alt": 560},
            "created_at": datetime.now(timezone.utc) - timedelta(days=90)
        },
        {
            "drone_id": "DRN-RBG-02",
            "name": "AgroScan Eagle X8",
            "model": "RBG Octocopter Precision Agro",
            "status": "IN_MISSION",
            "battery_level": 78,
            "max_flight_time_min": 42,
            "max_speed_kmh": 65.0,
            "max_altitude_m": 4500,
            "payload_types": ["Sensor Multiespectral MicaSense RedEdge-P", "Sensor Térmico Radiométrico", "Barómetro de Alta Precisión"],
            "operator_assigned": "Benjamin Garcia",
            "total_flight_hours": 88.0,
            "firmware": "v03.12.0110",
            "health_status": "EXCELLENT",
            "home_base": {"name": "Estación Agrícola Valle Central", "lat": -33.4450, "lng": -70.6620, "alt": 575},
            "created_at": datetime.now(timezone.utc) - timedelta(days=60)
        },
        {
            "drone_id": "DRN-RBG-03",
            "name": "PerimeterGuardian S4",
            "model": "SkyWatch Security Quad 4K",
            "status": "AVAILABLE",
            "battery_level": 100,
            "max_flight_time_min": 48,
            "max_speed_kmh": 90.0,
            "max_altitude_m": 5000,
            "payload_types": ["Cámara 4K Starlight RGB", "Detección IA de Intrusos a Bordo", "Sirena y Megáfono Remoto"],
            "operator_assigned": "Gustavo Jaramillo",
            "total_flight_hours": 215.3,
            "firmware": "v05.00.0042",
            "health_status": "GOOD",
            "home_base": {"name": "Puesto Avanzado Seguridad Perímetro", "lat": -33.4280, "lng": -70.6380, "alt": 590},
            "created_at": datetime.now(timezone.utc) - timedelta(days=120)
        },
        {
            "drone_id": "DRN-RBG-04",
            "name": "SolarInspector VTOL",
            "model": "Trinity F90+ Mapping & Thermal",
            "status": "MAINTENANCE",
            "battery_level": 45,
            "max_flight_time_min": 90,
            "max_speed_kmh": 115.0,
            "max_altitude_m": 6000,
            "payload_types": ["Sony RX1R II Full-Frame 42MP", "Sensor Termográfico 640x512"],
            "operator_assigned": "Rodrigo Tapia",
            "total_flight_hours": 310.8,
            "firmware": "v02.88.0019",
            "health_status": "INSPECTION_REQUIRED",
            "home_base": {"name": "Base Central RBG Santiago", "lat": -33.4372, "lng": -70.6506, "alt": 560},
            "created_at": datetime.now(timezone.utc) - timedelta(days=180)
        }
    ]
    db.drones.insert_many(drones_data)

    # 2. Missions Collection (Demonstrating Heterogeneous Waypoints)
    now = datetime.now(timezone.utc)
    missions_data = [
        {
            "mission_id": "MSN-2026-001",
            "name": "Inspección Termográfica y Estructural Subestación Eléctrica",
            "sector": "Industrial",
            "description": "Ruta de control para evaluar sobrecalentamiento en transformadores y capturar fotogrametría de alta resolución en torres de alta tensión.",
            "assigned_drone_id": "DRN-RBG-01",
            "drone_name": "SkySentinel Alpha V",
            "status": "COMPLETED",
            "created_by": "Rodrigo Tapia",
            "created_at": now - timedelta(hours=3),
            "started_at": now - timedelta(hours=2, minutes=45),
            "completed_at": now - timedelta(hours=2, minutes=20),
            "estimated_duration_min": 25,
            "actual_duration_min": 25,
            "safety_altitude_m": 45.0,
            "total_waypoints": 6,
            "total_distance_m": 2450,
            "battery_consumed_pct": 32,
            "waypoints": [
                {
                    "wp_num": 1,
                    "lat": -33.4372,
                    "lng": -70.6506,
                    "alt": 30.0,
                    "speed_ms": 5.0,
                    "action": "TAKEOFF_ASCEND",
                    "task_config": {
                        "type": "Despegue Vertical Seguro",
                        "climb_rate_ms": 2.5,
                        "hover_sec": 5,
                        "check_heading_deg": 45
                    }
                },
                {
                    "wp_num": 2,
                    "lat": -33.4348,
                    "lng": -70.6482,
                    "alt": 55.0,
                    "speed_ms": 10.0,
                    "action": "PHOTO_CAPTURE",
                    "task_config": {
                        "type": "Captura Fotográfica Alta Resolución",
                        "camera": "RGB 48MP Wide Lens",
                        "iso": 100,
                        "shutter_speed": "1/1200s",
                        "aperture": "f/2.8",
                        "gimbal_pitch_deg": -45,
                        "target_component": "Aislador Transformador TR-01",
                        "burst_photos": 3
                    }
                },
                {
                    "wp_num": 3,
                    "lat": -33.4325,
                    "lng": -70.6455,
                    "alt": 50.0,
                    "speed_ms": 6.0,
                    "action": "THERMAL_SCAN",
                    "task_config": {
                        "type": "Escaneo Térmico Radiométrico",
                        "sensor": "FLIR Vue Pro R 640",
                        "palette": "IronBow",
                        "emissivity": 0.95,
                        "temp_alarm_celsius": 75.0,
                        "target": "Barras de Conexión de Alta Tensión",
                        "ambient_temp_c": 22.5,
                        "record_radiometric_video": True
                    }
                },
                {
                    "wp_num": 4,
                    "lat": -33.4310,
                    "lng": -70.6490,
                    "alt": 60.0,
                    "speed_ms": 4.0,
                    "action": "HOVER_PANORAMA_360",
                    "task_config": {
                        "type": "Giro Panorámico Estabilizado 360°",
                        "duration_sec": 20,
                        "rotation_deg_per_sec": 18,
                        "shots_per_rotation": 8,
                        "overlap_percent": 75
                    }
                },
                {
                    "wp_num": 5,
                    "lat": -33.4338,
                    "lng": -70.6522,
                    "alt": 40.0,
                    "speed_ms": 8.0,
                    "action": "LIDAR_POINT_CLOUD",
                    "task_config": {
                        "type": "Escaneo Láser LIDAR Superficial",
                        "pulse_rate_khz": 240,
                        "points_per_m2": 150,
                        "return_mode": "Dual Returns"
                    }
                },
                {
                    "wp_num": 6,
                    "lat": -33.4372,
                    "lng": -70.6506,
                    "alt": 0.0,
                    "speed_ms": 3.0,
                    "action": "RETURN_TO_HOME_LAND",
                    "task_config": {
                        "type": "Aterrizaje Autónomo con Sensores Inferiores",
                        "precision_pad_detection": True,
                        "descent_speed_ms": 1.2
                    }
                }
            ]
        },
        {
            "mission_id": "MSN-2026-002",
            "name": "Monitoreo Multiespectral de Vigor Vegetativo y Estrés Hídrico",
            "sector": "Agrícola",
            "description": "Vuelo de escaneo automatizado para generación de mapas de índice NDVI y detección de fugas en líneas de riego por goteo.",
            "assigned_drone_id": "DRN-RBG-02",
            "drone_name": "AgroScan Eagle X8",
            "status": "IN_PROGRESS",
            "created_by": "Benjamin Garcia",
            "created_at": now - timedelta(minutes=45),
            "started_at": now - timedelta(minutes=15),
            "completed_at": None,
            "estimated_duration_min": 35,
            "actual_duration_min": 15,
            "safety_altitude_m": 60.0,
            "total_waypoints": 5,
            "total_distance_m": 3800,
            "battery_consumed_pct": 22,
            "waypoints": [
                {
                    "wp_num": 1,
                    "lat": -33.4450,
                    "lng": -70.6620,
                    "alt": 40.0,
                    "speed_ms": 6.0,
                    "action": "TAKEOFF_ASCEND",
                    "task_config": {
                        "type": "Despegue Inicial",
                        "climb_rate_ms": 3.0,
                        "hover_sec": 3
                    }
                },
                {
                    "wp_num": 2,
                    "lat": -33.4420,
                    "lng": -70.6590,
                    "alt": 60.0,
                    "speed_ms": 12.0,
                    "action": "MULTISPECTRAL_SCAN",
                    "task_config": {
                        "type": "Adquisición Multiespectral NDVI",
                        "bands": ["Green (560nm)", "Red (668nm)", "RedEdge (717nm)", "Near-IR (842nm)"],
                        "ground_sampling_distance_cm": 4.5,
                        "sun_sensor_calibration": "Done (DLS-2)"
                    }
                },
                {
                    "wp_num": 3,
                    "lat": -33.4390,
                    "lng": -70.6635,
                    "alt": 60.0,
                    "speed_ms": 12.0,
                    "action": "MULTISPECTRAL_SCAN",
                    "task_config": {
                        "type": "Adquisición Multiespectral Cuadrante B",
                        "bands": ["Red", "NIR"],
                        "overlap_forward_pct": 80,
                        "overlap_side_pct": 70
                    }
                },
                {
                    "wp_num": 4,
                    "lat": -33.4410,
                    "lng": -70.6670,
                    "alt": 50.0,
                    "speed_ms": 8.0,
                    "action": "THERMAL_IRRIGATION_CHECK",
                    "task_config": {
                        "type": "Inspección de Humedad del Suelo",
                        "thermal_contrast": "High",
                        "soil_saturation_alert": True
                    }
                },
                {
                    "wp_num": 5,
                    "lat": -33.4450,
                    "lng": -70.6620,
                    "alt": 0.0,
                    "speed_ms": 4.0,
                    "action": "RETURN_TO_HOME_LAND",
                    "task_config": {
                        "type": "RTH Automático",
                        "precision_pad_detection": True
                    }
                }
            ]
        },
        {
            "mission_id": "MSN-2026-003",
            "name": "Ronda Nocturna y Vigilancia Perimetral Automatizada",
            "sector": "Seguridad",
            "description": "Patrullaje perimetral continuo con reconocimiento óptico e infrarrojo en naves industriales y bodegas de almacenamiento.",
            "assigned_drone_id": "DRN-RBG-03",
            "drone_name": "PerimeterGuardian S4",
            "status": "PLANNED",
            "created_by": "Gustavo Jaramillo",
            "created_at": now - timedelta(hours=1),
            "started_at": None,
            "completed_at": None,
            "estimated_duration_min": 40,
            "actual_duration_min": 0,
            "safety_altitude_m": 50.0,
            "total_waypoints": 4,
            "total_distance_m": 2900,
            "battery_consumed_pct": 0,
            "waypoints": [
                {
                    "wp_num": 1,
                    "lat": -33.4280,
                    "lng": -70.6380,
                    "alt": 35.0,
                    "speed_ms": 7.0,
                    "action": "TAKEOFF_ASCEND",
                    "task_config": {
                        "type": "Despegue Táctico Silencioso",
                        "beacon_lights": "Off"
                    }
                },
                {
                    "wp_num": 2,
                    "lat": -33.4250,
                    "lng": -70.6350,
                    "alt": 45.0,
                    "speed_ms": 10.0,
                    "action": "AI_INTRUSION_DETECTION",
                    "task_config": {
                        "type": "Escaneo Inteligente Perímetro Norte",
                        "ai_model": "YOLO-V8 Aero Surveillance",
                        "target_classes": ["Person", "Vehicle", "Motion"],
                        "confidence_threshold": 0.85,
                        "auto_spotlight_on_detect": True
                    }
                },
                {
                    "wp_num": 3,
                    "lat": -33.4220,
                    "lng": -70.6390,
                    "alt": 45.0,
                    "speed_ms": 10.0,
                    "action": "PHOTO_CAPTURE",
                    "task_config": {
                        "type": "Registro Fotográfico Control Portón 3",
                        "camera": "Starlight Low-Light 4K",
                        "iso": 3200,
                        "shutter_speed": "1/200s",
                        "aperture": "f/1.8"
                    }
                },
                {
                    "wp_num": 4,
                    "lat": -33.4280,
                    "lng": -70.6380,
                    "alt": 0.0,
                    "speed_ms": 3.5,
                    "action": "RETURN_TO_HOME_LAND",
                    "task_config": {
                        "type": "Regreso a Base Segura"
                    }
                }
            ]
        }
    ]
    db.missions.insert_many(missions_data)

    # 3. Telemetry Collection (Demonstrating Time-Series burst data with timestamps)
    # Generate realistic telemetry points for completed mission MSN-2026-001
    telemetry_records = []
    base_time = now - timedelta(hours=2, minutes=45)
    start_lat, start_lng = -33.4372, -70.6506
    end_lat, end_lng = -33.4310, -70.6455
    total_steps = 100
    
    battery = 98.0
    alt = 0.0
    speed = 0.0
    motor_temp = 32.0

    for i in range(total_steps):
        t_sec = i * 15 # 1 reading every 15 seconds
        progress = i / float(total_steps)
        record_time = base_time + timedelta(seconds=t_sec)

        # Realistic flight physics curve
        if progress < 0.15: # Takeoff climb
            alt = min(55.0, alt + 3.8)
            speed = min(10.0, speed + 1.2)
        elif progress > 0.85: # Descent & land
            alt = max(0.0, alt - 3.2)
            speed = max(1.0, speed - 0.8)
        else:
            # Cruising with gentle altitude adjustments
            alt = 55.0 + math.sin(i * 0.3) * 4.5
            speed = 9.5 + math.cos(i * 0.2) * 2.1

        # Interpolate coordinates with waypoint noise
        current_lat = start_lat + (end_lat - start_lat) * math.sin(progress * math.pi)
        current_lng = start_lng + (end_lng - start_lng) * (1 - math.cos(progress * math.pi)) / 2.0

        # Battery consumption depends on speed and altitude climb
        climb_factor = 1.4 if progress < 0.15 else 1.0
        consumption_step = (0.28 * climb_factor) + (speed / 30.0) * 0.1
        battery = max(66.0, battery - consumption_step)

        # Motor temp increases with effort
        motor_temp = 32.0 + (1 - battery / 100.0) * 28.0 + random.uniform(-0.8, 1.2)
        
        telemetry_records.append({
            "mission_id": "MSN-2026-001",
            "drone_id": "DRN-RBG-01",
            "timestamp": record_time,
            "elapsed_seconds": t_sec,
            "gps": {
                "lat": round(current_lat + random.uniform(-0.00005, 0.00005), 6),
                "lng": round(current_lng + random.uniform(-0.00005, 0.00005), 6),
                "altitude_m": round(alt, 1),
                "relative_alt_m": round(alt, 1),
                "satellites": 18
            },
            "flight_dynamics": {
                "speed_ms": round(speed, 1),
                "speed_kmh": round(speed * 3.6, 1),
                "vertical_speed_ms": round(2.1 if progress < 0.15 else (-1.8 if progress > 0.85 else random.uniform(-0.3, 0.3)), 1),
                "pitch_deg": round(math.sin(i * 0.2) * 6.0, 1),
                "roll_deg": round(math.cos(i * 0.25) * 4.5, 1),
                "yaw_deg": round((i * 12.0) % 360, 1)
            },
            "power": {
                "battery_pct": round(battery, 1),
                "voltage_v": round(22.2 * (battery / 100.0) + 18.0 * (1 - battery / 100.0), 2),
                "current_a": round(14.5 + speed * 0.8 + random.uniform(-0.5, 0.5), 1),
                "power_w": round((14.5 + speed * 0.8) * 21.0, 1),
                "est_remaining_min": round((battery / 100.0) * 48.0, 1)
            },
            "diagnostics": {
                "motor_temp_c": round(motor_temp, 1),
                "esc_temp_c": round(motor_temp - 4.0, 1),
                "signal_rssi_dbm": random.randint(-68, -55),
                "wind_speed_kmh": round(8.5 + math.sin(i * 0.4) * 3.2, 1),
                "sensor_health": "NORMAL",
                "cpu_load_pct": random.randint(28, 44)
            }
        })

    # Also generate a few live telemetry readings for DRN-RBG-02 (Mission in progress)
    for j in range(25):
        t_sec = j * 15
        rec_time = (now - timedelta(minutes=15)) + timedelta(seconds=t_sec)
        telemetry_records.append({
            "mission_id": "MSN-2026-002",
            "drone_id": "DRN-RBG-02",
            "timestamp": rec_time,
            "elapsed_seconds": t_sec,
            "gps": {
                "lat": round(-33.4450 + (j * 0.0003), 6),
                "lng": round(-70.6620 + (j * 0.0002), 6),
                "altitude_m": 58.5 + random.uniform(-1, 1),
                "relative_alt_m": 58.5,
                "satellites": 20
            },
            "flight_dynamics": {
                "speed_ms": 11.8,
                "speed_kmh": 42.5,
                "vertical_speed_ms": 0.1,
                "pitch_deg": 3.2,
                "roll_deg": -1.5,
                "yaw_deg": 65.0
            },
            "power": {
                "battery_pct": round(96.0 - (j * 0.72), 1),
                "voltage_v": 21.8,
                "current_a": 16.2,
                "power_w": 353.1,
                "est_remaining_min": 32.0
            },
            "diagnostics": {
                "motor_temp_c": 38.5 + (j * 0.2),
                "esc_temp_c": 35.0,
                "signal_rssi_dbm": -60,
                "wind_speed_kmh": 12.0,
                "sensor_health": "NORMAL",
                "cpu_load_pct": 36
            }
        })

    db.telemetry.insert_many(telemetry_records)

    # 4. Telemetria_Misiones Collection (Modeling 1:1 with missions, embedded readings array)
    # Requisito Hito 50%: Colección 'telemetria_misiones' con relación 1:1 con misiones y lecturas embebidas.
    # Se extraen las lecturas de MSN-2026-001 y se almacenan como subdocumentos embebidos en 'lecturas'.
    m001_readings = [
        {
            "timestamp": r["timestamp"],
            "elapsed_seconds": r["elapsed_seconds"],
            "gps": r["gps"],
            "flight_dynamics": r["flight_dynamics"],
            "power": r["power"],
            "diagnostics": r["diagnostics"]
        }
        for r in telemetry_records if r.get("mission_id") == "MSN-2026-001"
    ]

    telemetria_misiones_data = [
        {
            "mission_id": "MSN-2026-001",
            "drone_id": "DRN-RBG-01",
            "created_at": now - timedelta(hours=2, minutes=45),
            "updated_at": now - timedelta(hours=2, minutes=20),
            "total_readings": len(m001_readings),
            "lecturas": m001_readings
        },
        {
            "mission_id": "MSN-2026-002",
            "drone_id": "DRN-RBG-02",
            "created_at": now - timedelta(minutes=15),
            "updated_at": now,
            "total_readings": 25,
            "lecturas": [
                {
                    "timestamp": r["timestamp"],
                    "elapsed_seconds": r["elapsed_seconds"],
                    "gps": r["gps"],
                    "flight_dynamics": r["flight_dynamics"],
                    "power": r["power"],
                    "diagnostics": r["diagnostics"]
                }
                for r in telemetry_records if r.get("mission_id") == "MSN-2026-002"
            ]
        }
    ]
    db.telemetria_misiones.insert_many(telemetria_misiones_data)

    # Ensure indexes (demonstrating MongoDB Time-Series and unique 1:1 relationships)
    try:
        db.telemetry.create_index([("mission_id", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])
        db.telemetry.create_index([("drone_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
        db.missions.create_index([("mission_id", pymongo.ASCENDING)], unique=True)
        db.drones.create_index([("drone_id", pymongo.ASCENDING)], unique=True)
        db.telemetria_misiones.create_index([("mission_id", pymongo.ASCENDING)], unique=True)
    except Exception as e:
        print(f">>> [Drones RBG] Índice creado o mockeado: {e}")

    print(f">>> [Drones RBG] Base de datos inicializada: {len(drones_data)} drones, {len(missions_data)} misiones, {len(telemetry_records)} registros de telemetría y {len(telemetria_misiones_data)} registros 1:1 en telemetria_misiones.")
    return True


# ==============================================================================
# Backend CRUD y Consultas de MongoDB (Requisito Hito 50%)
# ==============================================================================

def create_mission(mission_data):
    """
    CRUD: Crear una misión con waypoints embebidos.
    Utiliza insert_one de PyMongo garantizando la relación 1:N entre Drone y Misiones.
    Crea además el documento base en telemetria_misiones para la relación 1:1.
    """
    db = get_db()
    
    # Validar campos básicos
    if not mission_data.get("mission_id"):
        count = db.missions.count_documents({}) + 1
        mission_data["mission_id"] = f"MSN-2026-{str(count).zfill(3)}"
    
    if "created_at" not in mission_data:
        mission_data["created_at"] = datetime.now(timezone.utc)
    if "waypoints" not in mission_data:
        mission_data["waypoints"] = []
    
    mission_data["total_waypoints"] = len(mission_data["waypoints"])

    result = db.missions.insert_one(mission_data)
    mission_data["_id"] = result.inserted_id

    # Inicializar registro 1:1 en telemetria_misiones
    db.telemetria_misiones.update_one(
        {"mission_id": mission_data["mission_id"]},
        {
            "$setOnInsert": {
                "mission_id": mission_data["mission_id"],
                "drone_id": mission_data.get("assigned_drone_id"),
                "created_at": mission_data["created_at"],
                "updated_at": mission_data["created_at"],
                "total_readings": 0,
                "lecturas": []
            }
        },
        upsert=True
    )

    return mission_data


def register_telemetry_reading(mission_id, reading_data):
    """
    CRUD: Registrar telemetría simulada usando el operador $push (update_one).
    Empuja una nueva lectura embebida en el array 'lecturas' del documento 1:1 de telemetria_misiones
    e incrementa el contador de lecturas de forma atómica.
    También mantiene compatibilidad insertando el registro plano en db.telemetry.
    """
    db = get_db()
    now = datetime.now(timezone.utc)
    if "timestamp" not in reading_data:
        reading_data["timestamp"] = now

    # 1. Registrar con operador $push en telemetria_misiones (relación 1:1, lecturas embebidas)
    result = db.telemetria_misiones.update_one(
        {"mission_id": mission_id},
        {
            "$push": {"lecturas": reading_data},
            "$inc": {"total_readings": 1},
            "$set": {
                "updated_at": now,
                "drone_id": reading_data.get("drone_id")
            }
        },
        upsert=True
    )

    # 2. Mantener db.telemetry para compatibilidad total con vistas y gráficos existentes
    telemetry_flat = dict(reading_data)
    telemetry_flat["mission_id"] = mission_id
    db.telemetry.insert_one(telemetry_flat)

    return result.acknowledged


def get_missions_by_drone(drone_id):
    """
    CRUD: Consultar el historial de misiones por dron mediante db.missions.find().
    Demuestra la relación 1:N entre la colección 'drones' y 'missions'.
    """
    db = get_db()
    cursor = db.missions.find({"assigned_drone_id": drone_id}).sort("created_at", -1)
    return list(cursor)


def get_telemetry_by_mission(mission_id):
    """
    Consulta el documento 1:1 de telemetria_misiones para una misión dada.
    """
    db = get_db()
    doc = db.telemetria_misiones.find_one({"mission_id": mission_id})
    return doc


def update_mission(mission_id, update_fields):
    """
    CRUD: Actualizar atributos de una misión usando el operador $set (update_one).
    Permite modificar estado, tiempos o waypoints de forma atómica.
    """
    db = get_db()
    now = datetime.now(timezone.utc)
    update_fields["updated_at"] = now
    result = db.missions.update_one(
        {"mission_id": mission_id},
        {"$set": update_fields}
    )
    return result.modified_count > 0


def complete_mission(mission_id):
    """
    CRUD: Concluir y aprobar una misión operativa.
    Actualiza el estado de la misión a 'COMPLETED', fija 'completed_at',
    y libera la aeronave asignada en la colección 'drones' fijando su estado en 'AVAILABLE'.
    """
    db = get_db()
    mission = db.missions.find_one({"mission_id": mission_id})
    if not mission:
        return False, "Misión no encontrada"

    now = datetime.now(timezone.utc)
    assigned_drone_id = mission.get("assigned_drone_id")

    # 1. Actualizar estado de la misión en MongoDB
    db.missions.update_one(
        {"mission_id": mission_id},
        {"$set": {
            "status": "COMPLETED",
            "completed_at": now,
            "updated_at": now
        }}
    )

    # 2. Liberar el dron en la colección 'drones'
    if assigned_drone_id:
        db.drones.update_one(
            {"drone_id": assigned_drone_id},
            {"$set": {
                "status": "AVAILABLE",
                "last_mission_completed_at": now
            }}
        )

    return True, f"Misión {mission_id} completada exitosamente y dron {assigned_drone_id} liberado a AVAILABLE."


def delete_mission(mission_id):
    """
    CRUD: Eliminar una misión y su telemetría asociada (delete_one y delete_many).
    Mantiene la integridad referencial entre colecciones de MongoDB.
    """
    db = get_db()
    result_m = db.missions.delete_one({"mission_id": mission_id})
    db.telemetria_misiones.delete_one({"mission_id": mission_id})
    db.telemetry.delete_many({"mission_id": mission_id})
    return result_m.deleted_count > 0


def create_drone(drone_data):
    """
    CRUD: Registrar una nueva aeronave / dron en la colección 'drones' de MongoDB.
    Valida unicidad de 'drone_id' y establece atributos aeroespaciales estándar.
    """
    db = get_db()
    drone_id = (drone_data.get("drone_id") or "").strip().upper()
    if not drone_id:
        count = db.drones.count_documents({}) + 1
        drone_id = f"DRN-RBG-{str(count).zfill(2)}"

    # Verificar unicidad de drone_id
    existing = db.drones.find_one({"drone_id": drone_id})
    if existing:
        raise ValueError(f"Ya existe una aeronave registrada con el identificador '{drone_id}'.")

    now = datetime.now(timezone.utc)
    
    # Procesar payloads / sensores
    payloads = drone_data.get("payload_types", [])
    if isinstance(payloads, str):
        payloads = [p.strip() for p in payloads.split(",") if p.strip()]
    if not payloads:
        payloads = ["Cámara RGB 48MP"]

    new_drone = {
        "drone_id": drone_id,
        "name": (drone_data.get("name") or "Aeronave RBG").strip(),
        "model": (drone_data.get("model") or "Quadcopter Táctico Multi-Sensor").strip(),
        "status": drone_data.get("status", "AVAILABLE"),
        "battery_level": int(drone_data.get("battery_level", 100)),
        "max_flight_time_min": int(drone_data.get("max_flight_time_min", 45)),
        "max_speed_kmh": float(drone_data.get("max_speed_kmh", 75.0)),
        "max_altitude_m": float(drone_data.get("max_altitude_m", 5000.0)),
        "payload_types": payloads,
        "operator_assigned": drone_data.get("operator_assigned", "Rodrigo Tapia"),
        "total_flight_hours": float(drone_data.get("total_flight_hours", 0.0)),
        "firmware": drone_data.get("firmware", "v01.00.0001"),
        "health_status": drone_data.get("health_status", "EXCELLENT"),
        "home_base": drone_data.get("home_base", {
            "name": "Base Central RBG Santiago",
            "lat": -33.4372,
            "lng": -70.6506,
            "alt": 560.0
        }),
        "created_at": now
    }

    result = db.drones.insert_one(new_drone)
    new_drone["_id"] = result.inserted_id
    return new_drone


