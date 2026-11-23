// ==============================================================================
// DRONES RBG - SCRIPT OFICIAL MONGODB (INICIALIZACIÓN, ESQUEMA E ÍNDICES)
// Base de Datos: drones_rbg
// Requisito Hito 50%: Scripts de MongoDB (Creación de colecciones, índices y datos de prueba)
// Puede ejecutarse directamente en mongosh: mongosh drones_rbg mongo_setup.js
// ==============================================================================

use drones_rbg;

print(">>> [MongoDB Setup] Iniciando configuración de Drones RBG...");

// 1. Limpieza inicial opcional
db.drones.drop();
db.missions.drop();
db.telemetria_misiones.drop();
db.telemetry.drop();

// 2. Creación explícita de colecciones con Reglas de Validación de Esquema (Schema Validation)
// Requisito Rúbrica Oficial (Semanas 3, 6 e Hito Final): Reglas de validación, tipos y enums
print(">>> [MongoDB Setup] Creando colecciones con $jsonSchema Validation...");

db.createCollection("drones", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["drone_id", "name", "model", "status", "battery_level"],
      properties: {
        drone_id: {
          bsonType: "string",
          description: "Identificador alfanumérico único obligatorio (ej. DRN-RBG-01)"
        },
        name: {
          bsonType: "string",
          description: "Nombre táctico de la aeronave"
        },
        model: {
          bsonType: "string",
          description: "Modelo industrial del dron"
        },
        status: {
          enum: ["AVAILABLE", "IN_MISSION", "MAINTENANCE"],
          description: "Estado operativo estrictamente tipado"
        },
        battery_level: {
          bsonType: ["int", "double"],
          minimum: 0,
          maximum: 100,
          description: "Nivel de batería entre 0 y 100%"
        },
        payload_types: {
          bsonType: "array",
          description: "Sensores y cargas útiles instaladas"
        }
      }
    }
  },
  validationLevel: "moderate",
  validationAction: "warn"
});

db.createCollection("missions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["mission_id", "name", "sector", "assigned_drone_id", "status", "waypoints"],
      properties: {
        mission_id: {
          bsonType: "string",
          description: "Identificador único de la misión obligatorio (ej. MSN-2026-001)"
        },
        name: {
          bsonType: "string",
          description: "Nombre de la operación"
        },
        sector: {
          enum: ["Industrial", "Agrícola", "Seguridad"],
          description: "Sector productivo clasificado"
        },
        assigned_drone_id: {
          bsonType: "string",
          description: "Identificador del dron asignado (relación 1:N)"
        },
        status: {
          enum: ["PLANNED", "IN_PROGRESS", "COMPLETED", "ABORTED"],
          description: "Estado del ciclo de vida de la misión"
        },
        waypoints: {
          bsonType: "array",
          minItems: 1,
          description: "Arreglo embebido con al menos 1 punto de navegación heterogéneo"
        }
      }
    }
  },
  validationLevel: "moderate",
  validationAction: "warn"
});

db.createCollection("telemetria_misiones");
db.createCollection("telemetry");

// 3. Creación de Índices de Rendimiento y Unicidad
print(">>> [MongoDB Setup] Creando índices...");

// Índices en 'drones'
db.drones.createIndex({ "drone_id": 1 }, { unique: true, name: "idx_drones_drone_id_unique" });
db.drones.createIndex({ "status": 1 }, { name: "idx_drones_status" });

// Índices en 'missions' (Relación 1:N con drones por assigned_drone_id)
db.missions.createIndex({ "mission_id": 1 }, { unique: true, name: "idx_missions_id_unique" });
db.missions.createIndex({ "assigned_drone_id": 1, "created_at": -1 }, { name: "idx_missions_drone_history" });
db.missions.createIndex({ "status": 1 }, { name: "idx_missions_status" });

// Índices en 'telemetria_misiones' (Relación 1:1 con missions por mission_id)
db.telemetria_misiones.createIndex({ "mission_id": 1 }, { unique: true, name: "idx_telemetria_mission_id_unique" });

// Índices en 'telemetry' (Serie Temporal Append-Only)
db.telemetry.createIndex({ "mission_id": 1, "timestamp": 1 }, { name: "idx_telemetry_mission_ts" });
db.telemetry.createIndex({ "drone_id": 1, "timestamp": -1 }, { name: "idx_telemetry_drone_ts" });

// 4. Inserción de Datos de Prueba (Seed Data)
print(">>> [MongoDB Setup] Insertando flota de drones...");
const now = new Date();

db.drones.insertMany([
  {
    drone_id: "DRN-RBG-01",
    name: "SkySentinel Alpha V",
    model: "DJI Matrice 350 RTK Industrial",
    status: "AVAILABLE",
    battery_level: 94,
    max_flight_time_min: 55,
    max_speed_kmh: 82.8,
    max_altitude_m: 7000,
    payload_types: ["Cámara Zenmuse H20T (Térmica + Zoom 200x)", "Telémetro Láser (LIDAR)", "Foco Nocturno"],
    operator_assigned: "Rodrigo Tapia",
    total_flight_hours: 142.5,
    firmware: "v04.01.0205",
    health_status: "EXCELLENT",
    home_base: { name: "Base Central RBG Santiago", lat: -33.4372, lng: -70.6506, alt: 560 },
    created_at: new Date(now.getTime() - 90 * 24 * 3600 * 1000)
  },
  {
    drone_id: "DRN-RBG-02",
    name: "AgroScan Eagle X8",
    model: "RBG Octocopter Precision Agro",
    status: "IN_MISSION",
    battery_level: 78,
    max_flight_time_min: 42,
    max_speed_kmh: 65.0,
    max_altitude_m: 4500,
    payload_types: ["Sensor Multiespectral MicaSense RedEdge-P", "Sensor Térmico Radiométrico", "Barómetro de Alta Precisión"],
    operator_assigned: "Benjamin Garcia",
    total_flight_hours: 88.0,
    firmware: "v03.12.0110",
    health_status: "EXCELLENT",
    home_base: { name: "Estación Agrícola Valle Central", lat: -33.4450, lng: -70.6620, alt: 575 },
    created_at: new Date(now.getTime() - 60 * 24 * 3600 * 1000)
  },
  {
    drone_id: "DRN-RBG-03",
    name: "PerimeterGuardian S4",
    model: "SkyWatch Security Quad 4K",
    status: "AVAILABLE",
    battery_level: 100,
    max_flight_time_min: 48,
    max_speed_kmh: 90.0,
    max_altitude_m: 5000,
    payload_types: ["Cámara 4K Starlight RGB", "Detección IA de Intrusos a Bordo", "Sirena y Megáfono Remoto"],
    operator_assigned: "Gustavo Jaramillo",
    total_flight_hours: 215.3,
    firmware: "v05.00.0042",
    health_status: "GOOD",
    home_base: { name: "Puesto Avanzado Seguridad Perímetro", lat: -33.4280, lng: -70.6380, alt: 590 },
    created_at: new Date(now.getTime() - 120 * 24 * 3600 * 1000)
  },
  {
    drone_id: "DRN-RBG-04",
    name: "SolarInspector VTOL",
    model: "Trinity F90+ Mapping & Thermal",
    status: "MAINTENANCE",
    battery_level: 45,
    max_flight_time_min: 90,
    max_speed_kmh: 115.0,
    max_altitude_m: 6000,
    payload_types: ["Sony RX1R II Full-Frame 42MP", "Sensor Termográfico 640x512"],
    operator_assigned: "Rodrigo Tapia",
    total_flight_hours: 310.8,
    firmware: "v02.88.0019",
    health_status: "INSPECTION_REQUIRED",
    home_base: { name: "Base Central RBG Santiago", lat: -33.4372, lng: -70.6506, alt: 560 },
    created_at: new Date(now.getTime() - 180 * 24 * 3600 * 1000)
  }
]);

print(">>> [MongoDB Setup] Insertando misiones con waypoints heterogéneos (1:N con drones)...");
db.missions.insertMany([
  {
    mission_id: "MSN-2026-001",
    name: "Inspección Termográfica y Estructural Subestación Eléctrica",
    sector: "Industrial",
    description: "Ruta de control para evaluar sobrecalentamiento en transformadores.",
    assigned_drone_id: "DRN-RBG-01",
    drone_name: "SkySentinel Alpha V",
    status: "COMPLETED",
    created_by: "Rodrigo Tapia",
    created_at: new Date(now.getTime() - 3 * 3600 * 1000),
    started_at: new Date(now.getTime() - 2.75 * 3600 * 1000),
    completed_at: new Date(now.getTime() - 2.33 * 3600 * 1000),
    estimated_duration_min: 25,
    actual_duration_min: 25,
    safety_altitude_m: 45.0,
    total_waypoints: 3,
    total_distance_m: 2450,
    battery_consumed_pct: 32,
    waypoints: [
      {
        wp_num: 1,
        lat: -33.4372,
        lng: -70.6506,
        alt: 30.0,
        speed_ms: 5.0,
        action: "TAKEOFF_ASCEND",
        task_config: { type: "Despegue Vertical Seguro", hover_sec: 5 }
      },
      {
        wp_num: 2,
        lat: -33.4348,
        lng: -70.6482,
        alt: 55.0,
        speed_ms: 10.0,
        action: "PHOTO_CAPTURE",
        task_config: { type: "Captura Fotográfica Alta Resolución", camera: "RGB 48MP", iso: 100 }
      },
      {
        wp_num: 3,
        lat: -33.4325,
        lng: -70.6455,
        alt: 50.0,
        speed_ms: 6.0,
        action: "THERMAL_SCAN",
        task_config: { type: "Escaneo Térmico Radiométrico", palette: "IronBow", temp_alarm_celsius: 75.0 }
      }
    ]
  },
  {
    mission_id: "MSN-2026-002",
    name: "Monitoreo Multiespectral de Vigor Vegetativo",
    sector: "Agrícola",
    description: "Vuelo automatizado para mapas NDVI y estrés hídrico.",
    assigned_drone_id: "DRN-RBG-02",
    drone_name: "AgroScan Eagle X8",
    status: "IN_PROGRESS",
    created_by: "Benjamin Garcia",
    created_at: new Date(now.getTime() - 45 * 60 * 1000),
    started_at: new Date(now.getTime() - 15 * 60 * 1000),
    completed_at: null,
    estimated_duration_min: 35,
    safety_altitude_m: 60.0,
    total_waypoints: 2,
    total_distance_m: 3800,
    battery_consumed_pct: 22,
    waypoints: [
      {
        wp_num: 1,
        lat: -33.4450,
        lng: -70.6620,
        alt: 40.0,
        speed_ms: 6.0,
        action: "TAKEOFF_ASCEND",
        task_config: { type: "Despegue Inicial", climb_rate_ms: 3.0 }
      },
      {
        wp_num: 2,
        lat: -33.4420,
        lng: -70.6590,
        alt: 60.0,
        speed_ms: 12.0,
        action: "MULTISPECTRAL_SCAN",
        task_config: { type: "NDVI", bands: ["Green", "Red", "NIR"] }
      }
    ]
  },
  {
    mission_id: "MSN-2026-003",
    name: "Ronda Nocturna y Vigilancia Perimetral",
    sector: "Seguridad",
    description: "Patrullaje perimetral continuo con reconocimiento óptico e infrarrojo.",
    assigned_drone_id: "DRN-RBG-03",
    drone_name: "PerimeterGuardian S4",
    status: "PLANNED",
    created_by: "Gustavo Jaramillo",
    created_at: new Date(now.getTime() - 60 * 60 * 1000),
    started_at: null,
    completed_at: null,
    estimated_duration_min: 40,
    safety_altitude_m: 50.0,
    total_waypoints: 2,
    total_distance_m: 2900,
    battery_consumed_pct: 0,
    waypoints: [
      {
        wp_num: 1,
        lat: -33.4280,
        lng: -70.6380,
        alt: 35.0,
        speed_ms: 7.0,
        action: "TAKEOFF_ASCEND",
        task_config: { type: "Despegue Táctico Silencioso" }
      },
      {
        wp_num: 2,
        lat: -33.4250,
        lng: -70.6350,
        alt: 45.0,
        speed_ms: 10.0,
        action: "AI_INTRUSION_DETECTION",
        task_config: { ai_model: "YOLO-V8 Aero Surveillance", auto_spotlight: true }
      }
    ]
  }
]);

print(">>> [MongoDB Setup] Insertando telemetría maestra (relación 1:1 con missions y array embebido 'lecturas')...");
db.telemetria_misiones.insertMany([
  {
    mission_id: "MSN-2026-001",
    drone_id: "DRN-RBG-01",
    created_at: new Date(now.getTime() - 2.75 * 3600 * 1000),
    updated_at: new Date(now.getTime() - 2.33 * 3600 * 1000),
    total_readings: 2,
    lecturas: [
      {
        timestamp: new Date(now.getTime() - 2.75 * 3600 * 1000),
        elapsed_seconds: 0,
        gps: { lat: -33.4372, lng: -70.6506, altitude_m: 0.0, satellites: 18 },
        flight_dynamics: { speed_kmh: 0.0, pitch_deg: 0.0, roll_deg: 0.0, yaw_deg: 0.0 },
        power: { battery_pct: 98.0, voltage_v: 22.2, power_w: 150.0 },
        diagnostics: { motor_temp_c: 32.0, signal_rssi_dbm: -58, sensor_health: "NORMAL" }
      },
      {
        timestamp: new Date(now.getTime() - 2.5 * 3600 * 1000),
        elapsed_seconds: 900,
        gps: { lat: -33.4348, lng: -70.6482, altitude_m: 55.0, satellites: 19 },
        flight_dynamics: { speed_kmh: 36.0, pitch_deg: 4.2, roll_deg: -1.0, yaw_deg: 45.0 },
        power: { battery_pct: 82.0, voltage_v: 21.4, power_w: 380.0 },
        diagnostics: { motor_temp_c: 41.5, signal_rssi_dbm: -62, sensor_health: "NORMAL" }
      }
    ]
  }
]);

print(">>> [MongoDB Setup] Insertando ráfagas serie temporal en 'telemetry'...");
db.telemetry.insertMany([
  {
    mission_id: "MSN-2026-001",
    drone_id: "DRN-RBG-01",
    timestamp: new Date(now.getTime() - 2.75 * 3600 * 1000),
    elapsed_seconds: 0,
    gps: { lat: -33.4372, lng: -70.6506, altitude_m: 0.0, satellites: 18 },
    flight_dynamics: { speed_kmh: 0.0 },
    power: { battery_pct: 98.0, voltage_v: 22.2, power_w: 150.0 },
    diagnostics: { motor_temp_c: 32.0, sensor_health: "NORMAL" }
  },
  {
    mission_id: "MSN-2026-001",
    drone_id: "DRN-RBG-01",
    timestamp: new Date(now.getTime() - 2.5 * 3600 * 1000),
    elapsed_seconds: 900,
    gps: { lat: -33.4348, lng: -70.6482, altitude_m: 55.0, satellites: 19 },
    flight_dynamics: { speed_kmh: 36.0 },
    power: { battery_pct: 82.0, voltage_v: 21.4, power_w: 380.0 },
    diagnostics: { motor_temp_c: 41.5, sensor_health: "NORMAL" }
  }
]);

print(">>> [MongoDB Setup] Estado actual de colecciones:");
print("• drones: " + db.drones.countDocuments() + " documentos.");
print("• missions: " + db.missions.countDocuments() + " documentos.");
print("• telemetria_misiones: " + db.telemetria_misiones.countDocuments() + " documentos.");
print("• telemetry: " + db.telemetry.countDocuments() + " documentos.");
print(">>> [MongoDB Setup] Finalizado exitosamente.");
