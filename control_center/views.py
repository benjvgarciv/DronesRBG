"""
Django views and JSON API endpoints for Drones RBG.
Provides interface controllers for the Flight Operator, Fleet Commander/Auditor,
and REST endpoints interacting directly with MongoDB via PyMongo.
"""

import json
from datetime import datetime, timezone
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .db_client import (
    get_db,
    get_db_status,
    serialize_doc,
    seed_database,
    create_drone,
    create_mission,
    complete_mission,
    delete_mission,
    get_missions_by_drone,
    get_telemetry_by_mission
)
from .services import (
    get_fleet_summary,
    get_mission_audit_analytics,
    simulate_live_telemetry_tick,
    get_sector_analytics_aggregation,
    get_waypoint_tasks_aggregation
)


def dashboard_view(request):
    """Main Mission Control Dashboard."""
    seed_database() # Ensure seed data exists
    summary = get_fleet_summary()
    db_status = get_db_status()
    sector_aggregations = get_sector_analytics_aggregation()
    task_aggregations = get_waypoint_tasks_aggregation()

    context = {
        "page_title": "Centro de Control de Telemetría y Misiones",
        "active_tab": "dashboard",
        "summary": summary,
        "db_status": db_status,
        "sector_aggregations": sector_aggregations,
        "task_aggregations": task_aggregations,
        "team_members": ["Rodrigo Tapia", "Benjamin Garcia", "Gustavo Jaramillo"]
    }
    return render(request, "dashboard.html", context)


def operator_view(request):
    """Flight Operator Hub: Interactive Waypoint Planner & Live Telemetry HUD."""
    seed_database()
    db = get_db()
    drones = list(db.drones.find({}))
    missions = list(db.missions.find({}).sort("created_at", -1))
    db_status = get_db_status()

    context = {
        "page_title": "Centro del Operador de Vuelo",
        "active_tab": "operator",
        "drones": serialize_doc(drones),
        "missions": serialize_doc(missions),
        "db_status": db_status,
        "team_members": ["Rodrigo Tapia", "Benjamin Garcia", "Gustavo Jaramillo"]
    }
    return render(request, "operator.html", context)


def commander_view(request):
    """Fleet Commander & Auditor Hub: Mission History, Analytics & BSON Inspector."""
    seed_database()
    db = get_db()

    # Filtros de búsqueda (Semana 5 / Hito 2)
    filter_sector = request.GET.get("sector", "").strip()
    filter_status = request.GET.get("status", "").strip()
    filter_drone = request.GET.get("drone_id", "").strip()

    query = {}
    if filter_sector and filter_sector != "ALL":
        query["sector"] = filter_sector
    if filter_status and filter_status != "ALL":
        query["status"] = filter_status
    if filter_drone and filter_drone != "ALL":
        query["assigned_drone_id"] = filter_drone

    missions = list(db.missions.find(query).sort("created_at", -1))
    drones = list(db.drones.find({}).sort("drone_id", 1))
    db_status = get_db_status()

    selected_mission_id = request.GET.get("mission_id")
    if not selected_mission_id and missions:
        # Default to first completed mission or first mission in filtered list
        completed = [m for m in missions if m.get("status") == "COMPLETED"]
        selected_mission_id = completed[0]["mission_id"] if completed else missions[0]["mission_id"]

    audit_data = get_mission_audit_analytics(selected_mission_id) if selected_mission_id else None
    telemetria_doc = get_telemetry_by_mission(selected_mission_id) if selected_mission_id else None

    # Pretty-formatted JSON string of the mission BSON document for clean display in code inspector
    pretty_mission_json = ""
    if audit_data and audit_data.get("mission"):
        pretty_mission_json = json.dumps(serialize_doc(audit_data["mission"]), indent=2, ensure_ascii=False)
    elif missions:
        pretty_mission_json = json.dumps(serialize_doc(missions[0]), indent=2, ensure_ascii=False)

    # Pre-serialized pure JSON data for Chart.js
    audit_data_json = json.dumps(serialize_doc(audit_data)) if audit_data else "{}"
    telemetria_doc_json = json.dumps(serialize_doc(telemetria_doc)) if telemetria_doc else "{}"

    # Extract last 5 readings for resilient fallback with flat, normalized keys
    raw_readings = []
    if telemetria_doc and isinstance(telemetria_doc.get("lecturas"), list):
        raw_readings = telemetria_doc["lecturas"][-5:]
        raw_readings.reverse()
    elif audit_data and audit_data.get("raw_telemetry_sample"):
        raw_readings = audit_data["raw_telemetry_sample"][:5]

    recent_readings = []
    for r in raw_readings:
        ts = str(r.get("timestamp", "N/A"))
        if len(ts) >= 19:
            time_str = ts[11:19]
        else:
            time_str = ts

        # Safely extract battery
        pwr = r.get("power", {}) if isinstance(r.get("power"), dict) else {}
        dyn = r.get("flight_dynamics", {}) if isinstance(r.get("flight_dynamics"), dict) else {}
        gps = r.get("gps", {}) if isinstance(r.get("gps"), dict) else {}
        diag = r.get("diagnostics", {}) if isinstance(r.get("diagnostics"), dict) else {}

        batt = pwr.get("battery_pct", r.get("bateria", 100))
        spd = dyn.get("speed_kmh", r.get("velocidad_kmh", 0))
        alt = gps.get("altitude_m", r.get("altitud_m", 0))
        pw = pwr.get("power_w", 240.0)
        temp = diag.get("motor_temp_c", r.get("temperatura_motor_c", 38.0))
        volt = pwr.get("voltage_v", 22.2)

        recent_readings.append({
            "time": time_str,
            "battery": batt,
            "speed": spd,
            "altitude": alt,
            "power": pw,
            "motor_temp": temp,
            "voltage": volt
        })

    sector_aggregations = get_sector_analytics_aggregation()
    task_aggregations = get_waypoint_tasks_aggregation()

    context = {
        "page_title": "Centro del Comandante de Flota y Auditoría",
        "active_tab": "commander",
        "missions": serialize_doc(missions),
        "drones": serialize_doc(drones),
        "selected_mission_id": selected_mission_id,
        "audit_data": audit_data,
        "audit_data_json": audit_data_json,
        "telemetria_doc": serialize_doc(telemetria_doc),
        "telemetria_doc_json": telemetria_doc_json,
        "pretty_mission_json": pretty_mission_json,
        "recent_readings": serialize_doc(recent_readings),
        "sector_aggregations": sector_aggregations,
        "task_aggregations": task_aggregations,
        "filter_sector": filter_sector,
        "filter_status": filter_status,
        "filter_drone": filter_drone,
        "distinct_sectors": ["Industrial", "Agrícola", "Seguridad"],
        "distinct_statuses": ["PLANNED", "IN_PROGRESS", "COMPLETED", "ABORTED"],
        "db_status": db_status,
        "team_members": ["Rodrigo Tapia", "Benjamin Garcia", "Gustavo Jaramillo"]
    }
    return render(request, "commander.html", context)


def architecture_view(request):
    """Technical architecture, Problem Statement & MongoDB vs SQL justification."""
    seed_database()
    db_status = get_db_status()

    context = {
        "page_title": "Arquitectura y Justificación Técnica",
        "active_tab": "architecture",
        "db_status": db_status,
        "team_members": ["Rodrigo Tapia", "Benjamin Garcia", "Gustavo Jaramillo"]
    }
    return render(request, "architecture.html", context)


# ==============================================================================
# REST API Endpoints (PyMongo Direct Interaction)
# ==============================================================================

def api_status(request):
    """Returns database status and document counts."""
    return JsonResponse(get_db_status())


@csrf_exempt
def api_drones_list(request):
    """
    CRUD Endpoint para 'drones':
    GET: Retorna el listado de todas las aeronaves en MongoDB.
    POST: Registra una nueva aeronave en la colección 'drones'.
    """
    db = get_db()

    if request.method == "GET":
        drones = list(db.drones.find({}).sort("drone_id", 1))
        return JsonResponse({"drones": serialize_doc(drones)})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Cuerpo de solicitud JSON no válido."}, status=400)

        name = data.get("name", "").strip()
        model = data.get("model", "").strip()
        if not name or not model:
            return JsonResponse({"error": "El nombre y el modelo de la aeronave son obligatorios."}, status=400)

        try:
            drone_doc = create_drone(data)
            return JsonResponse({
                "success": True,
                "message": f"Aeronave {drone_doc['drone_id']} registrada exitosamente en la flota.",
                "drone": serialize_doc(drone_doc)
            }, status=201)
        except ValueError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as exc:
            return JsonResponse({"error": f"Error al registrar aeronave: {str(exc)}"}, status=500)

    return HttpResponseBadRequest("Método no permitido")


@csrf_exempt
def api_missions_list_create(request):
    """
    GET: List all missions.
    POST: Create a new mission with heterogeneous waypoints in MongoDB.
    """
    db = get_db()

    if request.method == "GET":
        query = {}
        sector = request.GET.get("sector", "").strip()
        status = request.GET.get("status", "").strip()
        drone_id = request.GET.get("drone_id", "").strip()

        if sector and sector != "ALL":
            query["sector"] = sector
        if status and status != "ALL":
            query["status"] = status
        if drone_id and drone_id != "ALL":
            query["assigned_drone_id"] = drone_id

        missions = list(db.missions.find(query).sort("created_at", -1))
        return JsonResponse({"count": len(missions), "missions": serialize_doc(missions)})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return HttpResponseBadRequest("Invalid JSON body")

        name = data.get("name", "Misión de Vuelo RBG")
        sector = data.get("sector", "Industrial")
        drone_id = data.get("assigned_drone_id", "DRN-RBG-01")
        waypoints = data.get("waypoints", [])

        if not waypoints:
            return JsonResponse({"error": "Debe incluir al menos 1 waypoint"}, status=400)

        # Generate unique mission ID
        count = db.missions.count_documents({}) + 1
        mission_id = f"MSN-2026-{str(count).zfill(3)}"

        # Fetch drone info
        drone = db.drones.find_one({"drone_id": drone_id})
        drone_name = drone.get("name", "Drone No Identificado") if drone else "Drone Genérico"

        now = datetime.now(timezone.utc)
        mission_doc = {
            "mission_id": mission_id,
            "name": name,
            "sector": sector,
            "description": data.get("description", "Misión programada desde Centro de Control RBG"),
            "assigned_drone_id": drone_id,
            "drone_name": drone_name,
            "status": "PLANNED",
            "created_by": data.get("created_by", "Operador de Vuelo"),
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "estimated_duration_min": data.get("estimated_duration_min", len(waypoints) * 5),
            "safety_altitude_m": float(data.get("safety_altitude_m", 45.0)),
            "total_waypoints": len(waypoints),
            "total_distance_m": float(data.get("total_distance_m", 1850.0)),
            "battery_consumed_pct": 0,
            "waypoints": waypoints
        }

        # Use create_mission backend function (insert_one with 1:N and 1:1 initialization)
        mission_doc = create_mission(mission_doc)

        return JsonResponse({
            "success": True,
            "message": f"Misión {mission_id} programada y guardada exitosamente con {len(waypoints)} waypoints.",
            "mission": serialize_doc(mission_doc)
        }, status=201)

    return HttpResponseBadRequest("Method not allowed")


def api_drone_missions_history(request, drone_id):
    """
    CRUD Endpoint: Retorna el historial de misiones asignadas a un dron específico (relación 1:N).
    Usa db_client.get_missions_by_drone (find).
    """
    missions = get_missions_by_drone(drone_id)
    return JsonResponse({
        "drone_id": drone_id,
        "count": len(missions),
        "missions": serialize_doc(missions)
    })


def api_mission_detail(request, mission_id):
    """Returns single mission details."""
    db = get_db()
    mission = db.missions.find_one({"mission_id": mission_id})
    if not mission:
        return JsonResponse({"error": "Misión no encontrada"}, status=404)
    return JsonResponse({"mission": serialize_doc(mission)})


@csrf_exempt
def api_mission_complete(request, mission_id):
    """
    Segundo Flujo de Negocio: Concluir y aprobar una misión operativa.
    Actualiza el estado de la misión a 'COMPLETED' y libera el dron a 'AVAILABLE' en MongoDB.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Debe ser método POST")

    success, msg = complete_mission(mission_id)
    if not success:
        return JsonResponse({"error": msg}, status=404)

    return JsonResponse({
        "success": True,
        "message": msg,
        "mission_id": mission_id
    })


@csrf_exempt
def api_mission_delete(request, mission_id):
    """
    CRUD Endpoint: Eliminar permanentemente una misión y su telemetría asociada en MongoDB.
    """
    if request.method not in ("POST", "DELETE"):
        return HttpResponseBadRequest("Debe ser POST o DELETE")

    db = get_db()
    mission = db.missions.find_one({"mission_id": mission_id})
    if not mission:
        return JsonResponse({"error": "Misión no encontrada"}, status=404)

    drone_id = mission.get("assigned_drone_id")
    if drone_id:
        db.drones.update_one({"drone_id": drone_id}, {"$set": {"status": "AVAILABLE"}})

    deleted = delete_mission(mission_id)
    if not deleted:
        return JsonResponse({"error": "No se pudo eliminar la misión"}, status=500)

    return JsonResponse({
        "success": True,
        "message": f"Misión {mission_id} eliminada exitosamente del sistema.",
        "mission_id": mission_id
    })



def api_mission_telemetry(request, mission_id):
    """Returns all time-series telemetry records for a mission."""
    db = get_db()
    telemetry = list(db.telemetry.find({"mission_id": mission_id}).sort("timestamp", 1))
    return JsonResponse({
        "mission_id": mission_id,
        "count": len(telemetry),
        "telemetry": serialize_doc(telemetry)
    })


def api_mission_telemetria_doc(request, mission_id):
    """
    Returns single telemetria_misiones document (1:1 relation with embedded readings array).
    """
    doc = get_telemetry_by_mission(mission_id)
    if not doc:
        return JsonResponse({"error": "Telemetría 1:1 no encontrada"}, status=404)
    return JsonResponse({"telemetria_mision": serialize_doc(doc)})


def api_mission_audit(request, mission_id):
    """Returns audit analytics and time-series chart data for Fleet Commander."""
    audit = get_mission_audit_analytics(mission_id)
    if not audit:
        return JsonResponse({"error": "Misión no encontrada"}, status=404)
    return JsonResponse(audit)


@csrf_exempt
def api_simulate_step(request, mission_id):
    """Executes a single simulation tick and inserts telemetry burst into MongoDB."""
    if request.method != "POST":
        return HttpResponseBadRequest("Must be POST")
    
    step = request.GET.get("step")
    progress_step = int(step) if step is not None and step.isdigit() else None

    result = simulate_live_telemetry_tick(mission_id, progress_step)
    return JsonResponse(result)


@csrf_exempt
def api_reset_seed(request):
    """Resets database with fresh initial seed data."""
    if request.method != "POST":
        return HttpResponseBadRequest("Must be POST")
    seed_database(force=True)
    return JsonResponse({"success": True, "message": "Sistema y flota reinicializados con datos de prueba."})


def api_analytics_aggregations(request):
    """
    CRUD / Analytics: Retorna los resultados de las dos consultas de agregación nativas de MongoDB:
    1. Agregación 1: Auditoría de desempeño por sector ($group + $avg + $sum + $max + $project)
    2. Agregación 2: Demanda de tareas de waypoints ($unwind de waypoints embebidos + $group + $sort)
    """
    sectors = get_sector_analytics_aggregation()
    tasks = get_waypoint_tasks_aggregation()
    return JsonResponse({
        "success": True,
        "aggregation_1_sectors": sectors,
        "aggregation_2_waypoint_tasks": tasks
    })

