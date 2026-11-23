"""
Drones RBG - Suite Oficial de Pruebas Automatizadas
Requisito Rúbrica Final (Semana 7 y 8 - Criterio Pruebas: 5 Puntos)

Verifica los flujos principales del sistema, operaciones CRUD sobre MongoDB,
actualizaciones atómicas ($push, $set, $inc), agregaciones nativas y casos límite.
Ejecutar con: python manage.py test control_center
"""

from datetime import datetime, timezone
from django.test import TestCase
from django.urls import reverse
from control_center.db_client import (
    get_db,
    create_drone,
    create_mission,
    complete_mission,
    delete_mission,
    register_telemetry_reading,
    get_telemetry_by_mission
)
from control_center.services import (
    get_sector_analytics_aggregation,
    get_waypoint_tasks_aggregation
)


class DronesRBGMongoDBTests(TestCase):
    """Pruebas de persistencia, integridad referencial y operaciones NoSQL."""

    def setUp(self):
        """Inicializa referencias y limpia datos temporales de prueba."""
        self.db = get_db()
        self.test_drone_id = "DRN-TEST-UNIT"
        self.test_mission_id = "MSN-TEST-UNIT-01"

        # Limpiar cualquier residuo de pruebas previas
        self.db.drones.delete_one({"drone_id": self.test_drone_id})
        self.db.missions.delete_one({"mission_id": self.test_mission_id})
        self.db.telemetria_misiones.delete_one({"mission_id": self.test_mission_id})
        self.db.telemetry.delete_many({"mission_id": self.test_mission_id})

    def tearDown(self):
        """Limpieza garantizada post-test."""
        self.db.drones.delete_one({"drone_id": self.test_drone_id})
        self.db.missions.delete_one({"mission_id": self.test_mission_id})
        self.db.telemetria_misiones.delete_one({"mission_id": self.test_mission_id})
        self.db.telemetry.delete_many({"mission_id": self.test_mission_id})

    def test_01_mongodb_connectivity(self):
        """Verifica que la conexión a MongoDB esté activa y responda al comando ping."""
        client = self.db.client
        ping_result = client.admin.command('ping')
        self.assertEqual(ping_result.get('ok'), 1.0, "El servidor MongoDB debe responder ok=1.0 al ping")

    def test_02_create_drone_and_prevent_duplicate(self):
        """Caso Límite: Registro de dron y validación de unicidad de drone_id."""
        drone_data = {
            "drone_id": self.test_drone_id,
            "name": "Dron de Pruebas Unitarias",
            "model": "DJI Matrice Test Unit",
            "operator_assigned": "Rodrigo Tapia",
            "status": "AVAILABLE",
            "battery_level": 98,
            "payload_types": ["Cámara RGB 48MP", "Sensor Térmico FLIR"]
        }

        created = create_drone(drone_data)
        self.assertIsNotNone(created.get("_id"), "El dron debe persistirse y tener un ObjectId asignado")

        # Verificar en base de datos
        found = self.db.drones.find_one({"drone_id": self.test_drone_id})
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Dron de Pruebas Unitarias")

        # Caso límite: Intentar registrar el mismo identificador debe lanzar ValueError
        with self.assertRaises(ValueError):
            create_drone(drone_data)

    def test_03_create_mission_with_heterogeneous_waypoints(self):
        """Flujo 1: Creación de misión con waypoints heterogéneos y documento 1:1."""
        mission_data = {
            "mission_id": self.test_mission_id,
            "name": "Misión de Prueba NDVI y Térmica",
            "sector": "Agrícola",
            "assigned_drone_id": self.test_drone_id,
            "status": "PLANNED",
            "waypoints": [
                {
                    "wp_num": 1,
                    "action": "TAKEOFF_ASCEND",
                    "lat": -33.4500,
                    "lng": -70.6600,
                    "alt": 30.0,
                    "speed_ms": 5.0,
                    "task_config": {"climb_rate": 2.5}
                },
                {
                    "wp_num": 2,
                    "action": "MULTISPECTRAL_SCAN",
                    "lat": -33.4520,
                    "lng": -70.6630,
                    "alt": 55.0,
                    "speed_ms": 10.0,
                    "task_config": {"bands": ["Red", "NIR"], "target": "Viñedos"}
                }
            ]
        }

        created_mission = create_mission(mission_data)
        self.assertIsNotNone(created_mission.get("_id"))
        self.assertEqual(created_mission["total_waypoints"], 2)

        # Verificar que se creó automáticamente el documento 1:1 en telemetria_misiones
        telemetria_doc = get_telemetry_by_mission(self.test_mission_id)
        self.assertIsNotNone(telemetria_doc, "Debe existir un documento en telemetria_misiones con relación 1:1")
        self.assertEqual(telemetria_doc["total_readings"], 0)
        self.assertEqual(telemetria_doc["lecturas"], [])

    def test_04_atomic_telemetry_push(self):
        """Verifica actualización atómica con operador $push e $inc en subdocumentos embebidos."""
        # Crear misión base
        create_mission({
            "mission_id": self.test_mission_id,
            "name": "Misión Streaming Test",
            "sector": "Industrial",
            "assigned_drone_id": self.test_drone_id,
            "status": "IN_PROGRESS",
            "waypoints": [{"wp_num": 1, "action": "PHOTO_CAPTURE", "lat": -33.4, "lng": -70.6, "alt": 40.0}]
        })

        reading_packet = {
            "timestamp": datetime.now(timezone.utc),
            "elapsed_seconds": 15,
            "drone_id": self.test_drone_id,
            "gps": {"lat": -33.4370, "lng": -70.6500, "altitude_m": 42.0},
            "flight_dynamics": {"speed_kmh": 35.0},
            "power": {"battery_pct": 94.0, "power_w": 280.0},
            "diagnostics": {"motor_temp_c": 36.5, "sensor_health": "NORMAL"}
        }

        ack = register_telemetry_reading(self.test_mission_id, reading_packet)
        self.assertTrue(ack, "La inserción atómica de telemetría debe ser reconocida por MongoDB")

        # Verificar en telemetria_misiones ($push)
        doc = get_telemetry_by_mission(self.test_mission_id)
        self.assertEqual(doc["total_readings"], 1)
        self.assertEqual(len(doc["lecturas"]), 1)
        self.assertEqual(doc["lecturas"][0]["power"]["battery_pct"], 94.0)

    def test_05_native_aggregation_pipelines(self):
        """Verifica que las dos consultas de agregación ($group y $unwind) retornen estructuras válidas."""
        # Agregación 1: Sectores
        sectors = get_sector_analytics_aggregation()
        self.assertIsInstance(sectors, list, "La agregación de sectores debe retornar una lista")

        # Agregación 2: Tareas de waypoints
        tasks = get_waypoint_tasks_aggregation()
        self.assertIsInstance(tasks, list, "La agregación de tareas debe retornar una lista")

    def test_06_complete_and_delete_mission_business_flow(self):
        """Flujo 2: Concluir misión (liberar dron a AVAILABLE) y eliminación en cascada."""
        # 1. Registrar dron y misión
        create_drone({
            "drone_id": self.test_drone_id,
            "name": "Dron Flujo 2",
            "model": "Octocopter",
            "status": "IN_MISSION",
            "battery_level": 80
        })

        create_mission({
            "mission_id": self.test_mission_id,
            "name": "Misión Flujo 2",
            "sector": "Seguridad",
            "assigned_drone_id": self.test_drone_id,
            "status": "IN_PROGRESS",
            "waypoints": [{"wp_num": 1, "action": "PERIMETER_SURVEILLANCE", "lat": -33.4, "lng": -70.6, "alt": 50.0}]
        })

        # 2. Concluir misión
        ok, msg = complete_mission(self.test_mission_id)
        self.assertTrue(ok)

        mission_doc = self.db.missions.find_one({"mission_id": self.test_mission_id})
        drone_doc = self.db.drones.find_one({"drone_id": self.test_drone_id})

        self.assertEqual(mission_doc["status"], "COMPLETED")
        self.assertEqual(drone_doc["status"], "AVAILABLE", "El dron asignado debe liberarse a AVAILABLE")

        # 3. Eliminar misión
        deleted = delete_mission(self.test_mission_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.missions.find_one({"mission_id": self.test_mission_id}))
        self.assertIsNone(self.db.telemetria_misiones.find_one({"mission_id": self.test_mission_id}))
