"""
Models documentation and MongoDB Collection Schemas for Drones RBG.
Note: In this architecture, MongoDB is accessed natively via PyMongo (db_client.py)
to support flexible BSON subdocuments, dynamic polymorphic waypoints, and high-frequency time-series telemetry.

MongoDB Schema Specifications for Evaluation (Hito 50%):
=========================================================

1. Colección: 'drones'
   Representa la flota de aeronaves UAV.
   Campos:
     - _id: ObjectId
     - drone_id: String (Único, ej. "DRN-RBG-01")
     - name: String
     - model: String
     - status: String ("AVAILABLE", "IN_MISSION", "MAINTENANCE")
     - battery_level: Number (0 - 100)
     - max_flight_time_min: Number
     - max_speed_kmh: Number
     - max_altitude_m: Number
     - payload_types: Array[String]
     - operator_assigned: String
     - total_flight_hours: Number
     - firmware: String
     - health_status: String
     - home_base: Subdocument {name, lat, lng, alt}
     - created_at: ISODate

2. Colección: 'missions'
   Relación con Drones: 1:N (Un dron puede tener múltiples misiones; assigned_drone_id referencia drones.drone_id).
   Waypoints: Subdocumentos EMBEBIDOS con polimorfismo según el tipo de tarea.
   Campos:
     - _id: ObjectId
     - mission_id: String (Único, ej. "MSN-2026-001")
     - name: String
     - sector: String ("Industrial", "Agrícola", "Seguridad")
     - description: String
     - assigned_drone_id: String (Referencia a drones.drone_id)
     - drone_name: String
     - status: String ("PLANNED", "IN_PROGRESS", "COMPLETED")
     - created_by: String
     - created_at: ISODate
     - started_at: ISODate | null
     - completed_at: ISODate | null
     - estimated_duration_min: Number
     - safety_altitude_m: Number
     - total_waypoints: Number
     - total_distance_m: Number
     - battery_consumed_pct: Number
     - waypoints: Array de Subdocumentos Embebidos:
         [
           {
             "wp_num": 1,
             "lat": Float,
             "lng": Float,
             "alt": Float,
             "speed_ms": Float,
             "action": "PHOTO_CAPTURE" | "THERMAL_SCAN" | "HOVER_PANORAMA_360" | ...,
             "task_config": Subdocumento heterogéneo según la tarea (ISO, sensor, velocidad, etc.)
           }
         ]

3. Colección: 'telemetria_misiones'
   Relación con Misiones: 1:1 (Una misión tiene un único registro maestro de telemetría; mission_id único).
   Lecturas: Array de lecturas/ráfagas EMBEBIDAS actualizadas con el operador $push de PyMongo.
   Campos:
     - _id: ObjectId
     - mission_id: String (Único, relación 1:1 con missions.mission_id)
     - drone_id: String (Referencia al dron en misión)
     - created_at: ISODate
     - updated_at: ISODate
     - total_readings: Number (Contador atómico con $inc)
     - lecturas: Array de Subdocumentos Embebidos (Append-Only vía $push):
         [
           {
             "timestamp": ISODate,
             "elapsed_seconds": Number,
             "gps": { "lat": Float, "lng": Float, "altitude_m": Float, "satellites": Int },
             "flight_dynamics": { "speed_kmh": Float, "pitch_deg": Float, "roll_deg": Float, "yaw_deg": Float },
             "power": { "battery_pct": Float, "voltage_v": Float, "current_a": Float, "power_w": Float },
             "diagnostics": { "motor_temp_c": Float, "signal_rssi_dbm": Int, "sensor_health": String }
           }
         ]
"""

from django.db import models

# Django ORM models can remain minimal or empty since PyMongo is used directly.
