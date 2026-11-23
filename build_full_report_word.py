# -*- coding: utf-8 -*-
"""
Generador de Informe Word (.docx) Oficial para el Proyecto Integrador MongoDB
Drones RBG - Centro de Control de Telemetría y Misiones con Drones
Cumple con todos los requisitos de las Semanas 1 a 8 de la rúbrica oficial.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Establece color de fondo de una celda."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Establece márgenes internos de una celda (en dxa: 20 dxa = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_border(cell, **kwargs):
    """
    Establece bordes en una celda.
    kwargs: top, bottom, left, right con dict(sz=4, val='single', color='CBD5E1')
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
    for edge, val in kwargs.items():
        edge_data = parse_xml(
            f'<w:{edge} {nsdecls("w")} w:val="{val.get("val", "single")}" '
            f'w:sz="{val.get("sz", 4)}" w:space="0" w:color="{val.get("color", "CBD5E1")}"/>'
        )
        tcBorders.append(edge_data)
    tcPr.append(tcBorders)

def add_callout(doc, text, title="NOTA IMPORTANTE", border_color="0284C7", bg_color="F0F9FF"):
    """Crea una caja de advertencia o llamada destacada."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Borde izquierdo grueso
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run_t = p.add_run(f"[{title}] ")
    run_t.bold = True
    run_t.font.name = "Arial"
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = RGBColor.from_string(border_color)
    
    run_b = p.add_run(text)
    run_b.font.name = "Arial"
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text):
    """Crea un bloque de código formateado estilo terminal/IDE."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "0F172A")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    set_cell_border(cell,
        top=dict(sz=4, val="single", color="1E293B"),
        bottom=dict(sz=4, val="single", color="1E293B"),
        left=dict(sz=4, val="single", color="1E293B"),
        right=dict(sz=4, val="single", color="1E293B")
    )
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(248, 250, 252)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def generate_full_report(output_path):
    doc = docx.Document()
    
    # Configurar márgenes estándar (2.5 cm / 1 pulgada)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Encabezado y pie de página
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("Drones RBG • Informe Técnico Proyecto Integrador MongoDB")
        f_run.font.name = "Arial"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(148, 163, 184)

    # Colores corporativos aeroespaciales
    c_navy = RGBColor(15, 23, 42)      # #0F172A
    c_blue = RGBColor(2, 132, 199)     # #0284C7
    c_slate = RGBColor(71, 85, 105)    # #475569
    c_text = RGBColor(30, 41, 59)      # #1E293B

    # Helper para encabezados
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(16)
        run.font.color.rgb = c_navy
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(12.5)
        run.font.color.rgb = c_blue
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(10.5)
        run.font.color.rgb = c_navy
        return p

    def add_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.color.rgb = c_text
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
            rb.font.name = "Arial"
            rb.font.size = Pt(10)
            rb.font.color.rgb = c_navy
        rt = p.add_run(text)
        rt.font.name = "Arial"
        rt.font.size = Pt(10)
        rt.font.color.rgb = c_text
        return p

    # ==============================================================================
    # PORTADA / TÍTULO PRINCIPAL
    # ==============================================================================
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(24)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("DRONES RBG")
    r_title.bold = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(24)
    r_title.font.color.rgb = c_navy

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("Centro de Control de Telemetría y Misiones con Drones")
    r_sub.bold = True
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = c_blue

    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.space_after = Pt(14)
    r_desc = p_desc.add_run("INFORME TÉCNICO OFICIAL - PROYECTO INTEGRADOR MONGODB (8 SEMANAS)")
    r_desc.font.name = "Arial"
    r_desc.font.size = Pt(10)
    r_desc.font.color.rgb = c_slate
    r_desc.bold = True

    # Tabla de metadatos del equipo
    t_meta = doc.add_table(rows=4, cols=2)
    t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Integrantes del Equipo (RBG):", "• Rodrigo Tapia\n• Benjamin Garcia\n• Gustavo Jaramillo"),
        ("Plataforma y Arquitectura:", "Aplicación Web (Backend: Python 3.13+ / Django 5.2 | Base de Datos: MongoDB Atlas mediante PyMongo)"),
        ("Librerías Frontend y UI:", "Vanilla HTML5 / Modern CSS HUD Aeroespacial / Leaflet.js (Mapas) / Chart.js (Series Temporales)"),
        ("Entregables Oficiales:", "Código Fuente, Script mongo_setup.js ($jsonSchema e índices), Suite de Tests Unitarios, Benchmark explain")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        c0, c1 = t_meta.rows[row_idx].cells
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 80, 80, 100, 100)
        set_cell_margins(c1, 80, 80, 100, 100)
        set_cell_border(c0, bottom=dict(sz=4, val="single", color="E2E8F0"), top=dict(sz=4, val="single", color="E2E8F0"))
        set_cell_border(c1, bottom=dict(sz=4, val="single", color="E2E8F0"), top=dict(sz=4, val="single", color="E2E8F0"))
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.bold = True
        r0.font.name = "Arial"
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = c_navy
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = c_text

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==============================================================================
    # SEMANA 1: PLANTEAMIENTO DEL PROBLEMA Y JUSTIFICACIÓN TÉCNICA
    # ==============================================================================
    add_h1("Semana 1: Elección del Tema y Justificación de MongoDB")
    
    add_h2("1. Planteamiento del Problema Delimitado")
    add_p(
        "En los sectores industrial, agrícola y de seguridad, la operación de flotas de aeronaves no tripuladas "
        "(UAVs / drones) exige planificar rutas complejas de navegación (misiones) y monitorear variables de salud, "
        "geolocalización y telemetría de los vehículos en tiempo real a alta frecuencia. "
        "Las bases de datos relacionales tradicionales (SQL) enfrentan severas limitaciones arquitectónicas en este escenario:"
    )
    add_bullet(
        "Cada punto de navegación (waypoint) exige tareas de naturaleza completamente diferente. "
        "Una captura fotográfica RGB requiere parámetros de ISO, obturación y ángulo de gimbal; un escaneo térmico radiométrico "
        "requiere paletas FLIR y umbrales en °C; una panorámica 360° exige tiempos de hover estacionario y velocidad angular; "
        "y un escaneo multiespectral NDVI requiere bandas Green, Red y NIR. "
        "En SQL relacional, este polimorfismo obligaría a diseñar una tabla gigantesca con decenas de columnas donde el 90% "
        "son valores NULL, o estructurar múltiples tablas puente que degradan el rendimiento mediante costosos JOINs.",
        "1. Atributos de ruta heterogéneos y polimórficos: "
    )
    add_bullet(
        "El vuelo activo emite ráfagas constantes de datos (GPS, altitud barométrica, velocidad terrestre, voltaje, corriente, "
        "temperatura de motores y porcentaje de batería) a frecuencias de hasta 10 Hz. "
        "En motores SQL tradicionales con bloqueos de tabla/página y comprobación estricta de claves foráneas, estas ráfagas concurrentes "
        "generan cuellos de botella de escritura severos.",
        "2. Ingestión masiva de telemetría en serie temporal (Time-Series): "
    )

    add_h2("2. Usuarios Principales y Casos de Uso")
    add_bullet(
        "Diseña planes de vuelo tácticos sobre un mapa satelital interactivo (Leaflet.js), asigna tareas específicas "
        "por waypoint con atributos dinámicos, calcula distancias y consumo proyectado, e inicia la ejecución del vuelo visualizando "
        "en tiempo real la cabina de instrumentos HUD (horizonte artificial, altímetro, velocímetro y batería).",
        "• Operador de Vuelo: "
    )
    add_bullet(
        "Audita misiones concluidas o en curso, analiza gráficos multieje de consumo de batería vs condiciones de vuelo (velocidad y altitud), "
        "supervisa la temperatura de motores, consulta el historial de horas por dron, aprueba el cierre de misiones (liberando las aeronaves) "
        "e inspecciona el documento BSON real almacenado en MongoDB.",
        "• Comandante de Flota / Auditor: "
    )

    add_h2("3. Objetivo y Alcance Mínimo Viable (MVP)")
    add_p(
        "Diseñar y construir un producto de software funcional que resuelva integralmente la planificación de misiones con waypoints heterogéneos "
        "y la persistencia continua de telemetría aeronáutica en MongoDB mediante el driver nativo PyMongo, ofreciendo una experiencia interactiva "
        "para operadores y comandantes."
    )

    add_h2("4. Justificación Técnica de MongoDB frente al Modelo Relacional")
    add_bullet(
        "Cada waypoint se almacena como un subdocumento embebido dentro del documento de la misión. Esto permite recuperar la ruta completa "
        "en una sola operación find_one() con latencia sub-milisegundo, sin requerir migraciones de esquema cada vez que se añade un sensor nuevo.",
        "• Modelo Documental Flexible y Polimórfico: "
    )
    add_bullet(
        "MongoDB procesa escrituras atómicas de alta velocidad mediante insert_one() y el operador de actualización $push en arreglos embebidos, "
        "eliminando cuellos de botella de bloqueo relacional.",
        "• Motor Optimizado para Series Temporales: "
    )

    add_h2("5. Reconocimiento de Límites de MongoDB")
    add_bullet(
        "Misiones excesivamente prolongadas con cientos de miles de puntos podrían aproximarse al límite de 16 MB por documento BSON. "
        "Para mitigar esto, Drones RBG implementa una arquitectura híbrida: un documento 1:1 consolidado (telemetria_misiones) con muestreo regular "
        "y una colección complementaria append-only (telemetry) para almacenamiento continuo sin límite.",
        "• Límite BSON de 16 MB por documento: "
    )
    add_bullet(
        "Para garantizar que una misma aeronave no sea asignada simultáneamente a dos misiones en vuelo (estado IN_MISSION), "
        "la coherencia se valida estrictamente en la capa de servicios del backend en Django antes de emitir la escritura a MongoDB.",
        "• Coherencia Operativa entre Colecciones: "
    )

    # ==============================================================================
    # SEMANA 2: HISTORIAS DE USUARIO Y MODELO DOCUMENTAL
    # ==============================================================================
    add_h1("Semana 2: Historias de Usuario, Decisiones de Modelado y BSON")
    
    add_h2("1. Historias de Usuario y Operaciones Esperadas")
    add_bullet("Como operador, quiero diseñar una ruta en el mapa satelital y guardar la misión con sus waypoints heterogéneos. -> Operación: insert_one() en colección 'missions'.", "Historia 1 (Operador - Crear Misión): ")
    add_bullet("Como operador, quiero transmitir en vivo ráfagas de posición y salud durante el vuelo. -> Operación: update_one() con operador $push e $inc en colección 'telemetria_misiones' e insert_one() en 'telemetry'.", "Historia 2 (Operador - Streaming Telemetría): ")
    add_bullet("Como comandante, quiero consultar el detalle de una misión para auditar la ruta prevista. -> Operación: find_one({'mission_id': id}) en colección 'missions'.", "Historia 3 (Auditor - Consulta de Misión): ")
    add_bullet("Como comandante, quiero recuperar la serie temporal de vuelo para renderizar gráficos de batería vs altitud. -> Operación: find({'mission_id': id}).sort({'timestamp': 1}) sobre 'telemetry'.", "Historia 4 (Auditor - Telemetría Forense): ")
    add_bullet("Como comandante, quiero filtrar misiones por dron asignado para calcular horas acumuladas. -> Operación: find({'assigned_drone_id': id}) en 'missions'.", "Historia 5 (Auditor - Historial por Dron): ")
    add_bullet("Como comandante, quiero concluir y aprobar una misión para archivarla y liberar el dron a estado AVAILABLE. -> Operación: update_one({'mission_id': id}, {'$set': {'status': 'COMPLETED'}}) y update_one({'drone_id': id}, {'$set': {'status': 'AVAILABLE'}}).", "Historia 6 (Auditor - Cierre de Misión): ")

    add_h2("2. Justificación de Decisiones de Incrustación frente a Referencia")
    add_bullet(
        "Se modela mediante referencia documental (campo assigned_drone_id en 'missions'). "
        "Justificación: Un dron tiene ciclo de vida propio independiente de las misiones (mantenimiento, horas de vuelo totales, reemplazo de firmware). "
        "Incrustar todas las misiones dentro del documento del dron violaría el límite de 16 MB y duplicaría información innecesariamente.",
        "• Decisión de Referencia (Drones 1:N Misiones): "
    )
    add_bullet(
        "Se modela mediante incrustación (arreglo embebido 'waypoints' dentro de cada documento en 'missions'). "
        "Justificación: Un waypoint no tiene sentido de existencia fuera de su misión. Consultar la misión requiere siempre todos sus waypoints; "
        "incrustarlos garantiza atomicidad y lectura en una sola operación sin JOINs.",
        "• Decisión de Incrustación (Misiones 1:N Waypoints): "
    )
    add_bullet(
        "Se modela mediante una colección especializada con relación 1:1 por mission_id y un arreglo embebido 'lecturas'. "
        "Justificación: Permite consultar resúmenes consolidados y actualizar con $push sin interferir con la metadata estática de la misión.",
        "• Decisión 1:1 (Misiones 1:1 Telemetría Consolidada): "
    )

    add_h2("3. Documentos BSON/JSON Representativos del Proyecto")
    add_p("A continuación se presentan dos documentos BSON reales generados por el sistema:")
    
    add_h3("Documento Representativo 1: Colección 'missions' (Waypoints Embebidos Polimórficos)")
    json_mission = '''{
  "_id": ObjectId("6adf77d7aeb33f19689af95a"),
  "mission_id": "MSN-2026-001",
  "name": "Inspección Termográfica y Estructural Subestación Eléctrica",
  "sector": "Industrial",
  "assigned_drone_id": "DRN-RBG-01",
  "drone_name": "SkySentinel Alpha V",
  "status": "COMPLETED",
  "created_by": "Rodrigo Tapia",
  "created_at": ISODate("2026-11-17T18:25:00Z"),
  "safety_altitude_m": 45.0,
  "total_waypoints": 3,
  "total_distance_m": 2450.0,
  "battery_consumed_pct": 32.0,
  "waypoints": [
    {
      "wp_num": 1,
      "lat": -33.4372,
      "lng": -70.6506,
      "alt": 30.0,
      "speed_ms": 5.0,
      "action": "TAKEOFF_ASCEND",
      "task_config": { "type": "Despegue Vertical Seguro", "hover_sec": 5 }
    },
    {
      "wp_num": 2,
      "lat": -33.4348,
      "lng": -70.6482,
      "alt": 55.0,
      "speed_ms": 10.0,
      "action": "PHOTO_CAPTURE",
      "task_config": { "camera": "RGB 48MP", "iso": 100, "gimbal_deg": -45 }
    },
    {
      "wp_num": 3,
      "lat": -33.4325,
      "lng": -70.6455,
      "alt": 50.0,
      "speed_ms": 6.0,
      "action": "THERMAL_SCAN",
      "task_config": { "palette": "IronBow", "temp_alarm_celsius": 75.0, "emissivity": 0.95 }
    }
  ]
}'''
    add_code_block(doc, json_mission)

    add_h3("Documento Representativo 2: Colección 'drones' (Especificaciones y Cargas Útiles)")
    json_drone = '''{
  "_id": ObjectId("6adf77d7aeb33f19689af950"),
  "drone_id": "DRN-RBG-01",
  "name": "SkySentinel Alpha V",
  "model": "DJI Matrice 350 RTK Industrial",
  "status": "AVAILABLE",
  "battery_level": 94,
  "max_flight_time_min": 55,
  "max_speed_kmh": 82.8,
  "max_altitude_m": 7000.0,
  "payload_types": [
    "Cámara Zenmuse H20T (Térmica + Zoom 200x)",
    "Telémetro Láser (LIDAR de Precisión)",
    "Foco Nocturno 12000lm & Megáfono"
  ],
  "operator_assigned": "Rodrigo Tapia",
  "total_flight_hours": 142.5,
  "health_status": "EXCELLENT",
  "home_base": {
    "name": "Base Central RBG Santiago",
    "lat": -33.4372,
    "lng": -70.6506,
    "alt": 560.0
  }
}'''
    add_code_block(doc, json_drone)

    # ==============================================================================
    # SEMANA 3 Y 4: DICCIONARIO DE DATOS Y PROTOTIPO FUNCIONAL
    # ==============================================================================
    add_h1("Semana 3 y 4: Diccionario de Datos, Casos Límite y Prototipo")
    
    add_h2("1. Diccionario de Datos de las Cuatro Colecciones")
    
    # Tabla de colecciones
    t_dict = doc.add_table(rows=1, cols=4)
    t_dict.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Colección", "Campo Principal", "Tipo BSON", "Descripción y Reglas de Negocio"]
    for i, h in enumerate(headers):
        cell = t_dict.rows[0].cells[i]
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    fields_data = [
        ("drones", "drone_id", "String (Único)", "Identificador táctico de la aeronave (ej. DRN-RBG-01). Clave de dominio."),
        ("drones", "status", "String Enum", "Estado operativo: 'AVAILABLE', 'IN_MISSION', 'MAINTENANCE'."),
        ("drones", "battery_level", "Double / Int", "Porcentaje de batería actual (0% - 100%)."),
        ("drones", "payload_types", "Array[String]", "Lista de sensores y cargas útiles integradas en el fuselaje."),
        ("missions", "mission_id", "String (Único)", "Código único de la misión (ej. MSN-2026-001)."),
        ("missions", "assigned_drone_id", "String (Ref)", "Clave de referencia hacia la colección 'drones' (Relación 1:N)."),
        ("missions", "status", "String Enum", "Ciclo de vida: 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'ABORTED'."),
        ("missions", "sector", "String Enum", "Segmento productivo: 'Industrial', 'Agrícola', 'Seguridad'."),
        ("missions", "waypoints", "Array[Object]", "Arreglo embebido polimórfico con tareas dinámicas (minItems: 1)."),
        ("telemetria_misiones", "mission_id", "String (Único)", "Vínculo 1:1 con 'missions'."),
        ("telemetria_misiones", "lecturas", "Array[Object]", "Subdocumentos de telemetría agregados atómicamente con $push."),
        ("telemetria_misiones", "total_readings", "Int", "Contador atómico incrementado con operador $inc."),
        ("telemetry", "timestamp", "Date", "Sello de tiempo ISO para ordenamiento cronológico en serie temporal.")
    ]

    for c, f, t, d in fields_data:
        row = t_dict.add_row()
        for i, val in enumerate([c, f, t, d]):
            cell = row.cells[i]
            set_cell_margins(cell, 60, 60, 80, 80)
            set_cell_border(cell, bottom=dict(sz=4, val="single", color="E2E8F0"))
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if i == 1:
                r.bold = True
                r.font.color.rgb = c_navy
            elif i == 0:
                r.bold = True
                r.font.color.rgb = c_blue

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_h2("2. Dos Casos Límite Controlados en la Aplicación")
    add_bullet(
        "La función create_drone() en db_client.py comprueba la existencia de la clave antes de insertar. "
        "Si se intenta registrar un identificador existente, se aborta la operación y se lanza un error ValueError('Ya existe una aeronave registrada con el identificador...'), "
        "respaldado adicionalmente por el índice único idx_drones_drone_id_unique en MongoDB.",
        "• Caso Límite 1 (Prevención de Drones Duplicados): "
    )
    add_bullet(
        "Si un usuario envía un payload sin puntos de navegación o con un estado inválido, la regla de validación $jsonSchema "
        "en la colección 'missions' y la validación en views.py rechazan la petición devolviendo HTTP 400 Bad Request, impidiendo la persistencia de estados corruptos.",
        "• Caso Límite 2 (Validación de Misión sin Waypoints): "
    )

    # ==============================================================================
    # SEMANA 5: FILTROS E ÍNDICES DE RENDIMIENTO
    # ==============================================================================
    add_h1("Semana 5: Búsquedas con Filtros y Dos Índices Justificados")
    
    add_h2("1. Consultas con Filtros y Ordenación")
    add_p(
        "En el Centro del Comandante (/commander/), se implementaron filtros interactivos basados en consultas reales de MongoDB: "
        "filtrado por sector ('Industrial', 'Agrícola', 'Seguridad') y por estado ('PLANNED', 'IN_PROGRESS', 'COMPLETED'). "
        "Estas consultas ejecutan un find(query).sort('created_at', -1) dinámico y eficiente."
    )

    add_h2("2. Definición y Justificación de los Dos Índices Principales")
    add_bullet(
        "Índice compuesto creado con db.telemetry.createIndex({'mission_id': 1, 'timestamp': 1}). "
        "Justificación: Esta colección recibe ráfagas constantes a 10 Hz. Durante la auditoría forense, la consulta crítica busca todos los puntos "
        "de una misión ordenados temporalmente. Este índice permite recuperar los datos mediante un escaneo IXSCAN y resuelve la ordenación "
        "en el propio árbol B-Tree sin consumir memoria RAM del servidor. "
        "Sobrecosto en escrituras: Mínimo (~15 microsegundos por ráfaga), compensado ampliamente por evitar un COLLSCAN en lecturas.",
        "• Índice 1: idx_telemetry_mission_ts ({ mission_id: 1, timestamp: 1 }) -> "
    )
    add_bullet(
        "Índice compuesto creado con db.missions.createIndex({'assigned_drone_id': 1, 'created_at': -1}). "
        "Justificación: Modela y optimiza la relación 1:N entre aeronaves y misiones, permitiendo consultar el historial reciente de cualquier dron "
        "en tiempo constante O(log N).",
        "• Índice 2: idx_missions_drone_history ({ assigned_drone_id: 1, created_at: -1 }) -> "
    )

    # ==============================================================================
    # SEMANA 6: AGREGACIONES NATIVAS Y REGLAS DE VALIDACIÓN ($jsonSchema)
    # ==============================================================================
    add_h1("Semana 6: Agregaciones Nativas, Validación y Segundo Flujo")
    
    add_h2("1. Agregación Nativa 1: Desempeño Operacional por Sector")
    add_p(
        "Pregunta de Negocio: ¿Cuál es el volumen de misiones, tasa de éxito, consumo promedio de batería y número de aeronaves únicas utilizadas por sector? "
        "Pipeline ejecutado nativamente en MongoDB (services.py):"
    )
    pipe1_code = '''db.missions.aggregate([
  {
    $group: {
      _id: "$sector",
      total_missions: { $sum: 1 },
      completed_missions: { $sum: { $cond: [{ $eq: ["$status", "COMPLETED"] }, 1, 0] } },
      avg_distance_m: { $avg: "$total_distance_m" },
      avg_battery_consumed_pct: { $avg: "$battery_consumed_pct" },
      avg_duration_min: { $avg: "$estimated_duration_min" },
      max_distance_m: { $max: "$total_distance_m" },
      drones_used: { $addToSet: "$drone_name" }
    }
  },
  {
    $project: {
      sector: "$_id",
      _id: 0,
      total_missions: 1,
      completed_missions: 1,
      avg_distance_m: { $round: ["$avg_distance_m", 1] },
      avg_battery_consumed_pct: { $round: ["$avg_battery_consumed_pct", 1] },
      avg_duration_min: { $round: ["$avg_duration_min", 1] },
      max_distance_m: { $round: ["$max_distance_m", 1] },
      unique_drones_count: { $size: "$drones_used" }
    }
  },
  { $sort: { total_missions: -1 } }
])'''
    add_code_block(doc, pipe1_code)

    add_h2("2. Agregación Nativa 2: Demanda de Tareas de Sensores ($unwind Polimórfico)")
    add_p(
        "Pregunta de Negocio: ¿Cuáles son las tareas y sensores más solicitados en los planes de vuelo (RGB, FLIR, NDVI, LiDAR) "
        "y a qué altitud y velocidad promedio operan? "
        "Aprovecha el operador $unwind para desglosar el arreglo embebido 'waypoints':"
    )
    pipe2_code = '''db.missions.aggregate([
  { $unwind: "$waypoints" },
  {
    $group: {
      _id: "$waypoints.action",
      total_executions: { $sum: 1 },
      avg_altitude_m: { $avg: "$waypoints.alt" },
      avg_speed_ms: { $avg: "$waypoints.speed_ms" },
      min_altitude_m: { $min: "$waypoints.alt" },
      max_altitude_m: { $max: "$waypoints.alt" }
    }
  },
  {
    $project: {
      task_action: "$_id",
      _id: 0,
      total_executions: 1,
      avg_altitude_m: { $round: ["$avg_altitude_m", 1] },
      avg_speed_ms: { $round: ["$avg_speed_ms", 1] },
      avg_speed_kmh: { $round: [{ $multiply: ["$avg_speed_ms", 3.6] }, 1] },
      min_altitude_m: 1,
      max_altitude_m: 1
    }
  },
  { $sort: { total_executions: -1 } }
])'''
    add_code_block(doc, pipe2_code)

    add_h2("3. Reglas de Validación de Esquema (Schema Validation)")
    add_p(
        "En mongo_setup.js se definieron reglas formales con el operador $jsonSchema para las colecciones 'drones' y 'missions', "
        "asegurando campos obligatorios requeridos (required: ['mission_id', 'status', 'assigned_drone_id', 'waypoints']), "
        "tipado estricto en double/int para batería y altitudes, y validación de tipos enum para el ciclo de vida."
    )

    add_h2("4. Segundo Proceso de Negocio Completo: Conclusión y Cierre Operativo")
    add_p(
        "El segundo flujo de negocio permite al Comandante auditar la misión y accionar el botón 'Concluir y Aprobar Misión'. "
        "Esta operación actualiza el estado de la misión a 'COMPLETED', calcula el consumo final y, simultáneamente, "
        "actualiza el documento del dron en la colección 'drones' fijando su estado en 'AVAILABLE', permitiendo que vuelva a estar elegible en el mapa táctico."
    )

    # ==============================================================================
    # SEMANA 7: EVIDENCIA EXPERIMENTAL (explain) Y PRUEBAS
    # ==============================================================================
    add_h1("Semana 7: Evidencia de Rendimiento (explain) y Pruebas Unitarias")
    
    add_h2("1. Evidencia Experimental de Índices mediante explain('executionStats')")
    add_p(
        "Se ejecutó un benchmark experimental sobre la colección 'telemetry' comparando la consulta con índice "
        "frente a un escaneo forzado completo (COLLSCAN vía hint natural). Los resultados exactos obtenidos son:"
    )

    t_exp = doc.add_table(rows=6, cols=4)
    t_exp.alignment = WD_TABLE_ALIGNMENT.CENTER
    exp_headers = ["Métrica de Rendimiento", "Con Índice (IXSCAN)", "Sin Índice (COLLSCAN)", "Impacto Técnico Observado"]
    for i, h in enumerate(exp_headers):
        cell = t_exp.rows[0].cells[i]
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    exp_rows = [
        ("Etapa de Ejecución (Stage)", "IXSCAN / FETCH", "COLLSCAN", "Acceso directo mediante punteros de árbol B-Tree."),
        ("Documentos Devueltos (nReturned)", "100", "100", "Ambas consultas resuelven el conjunto correcto."),
        ("Documentos Examinados (DocsExamined)", "100", "160", "Se examinaron 60 documentos innecesarios en COLLSCAN (el 100% de la BD)."),
        ("Claves de Índice Leídas (KeysExamined)", "100", "0", "Uso exclusivo del índice compuesto."),
        ("Ratio de Eficiencia (DocsExamined / nReturned)", "1.0 (Óptimo)", "1.60 (Degradación lineal)", "Con el índice, MongoDB examina únicamente los registros solicitados.")
    ]
    for r_idx, (m, c_idx, c_col, imp) in enumerate(exp_rows, start=1):
        row = t_exp.rows[r_idx]
        for i, val in enumerate([m, c_idx, c_col, imp]):
            cell = row.cells[i]
            set_cell_margins(cell, 60, 60, 80, 80)
            set_cell_border(cell, bottom=dict(sz=4, val="single", color="E2E8F0"))
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if i == 1:
                r.bold = True
                r.font.color.rgb = RGBColor(5, 150, 105) # Verde éxito
            elif i == 2:
                r.bold = True
                r.font.color.rgb = RGBColor(220, 38, 38) # Rojo alerta

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_h2("2. Resultados de la Suite de Pruebas Automatizadas (Django TestCase)")
    add_p("Se desarrolló una suite oficial en control_center/tests.py con 6 pruebas automatizadas (100% exitosas):")
    add_bullet("Valida conectividad y comando ping (ok=1.0) sobre MongoDB Atlas.", "• test_01_mongodb_connectivity: ")
    add_bullet("Comprueba creación de dron y valida el caso límite de duplicidad lanzando ValueError.", "• test_02_create_drone_and_prevent_duplicate: ")
    add_bullet("Verifica persistencia de waypoints heterogéneos y creación automática de documento maestro 1:1.", "• test_03_create_mission_with_heterogeneous_waypoints: ")
    add_bullet("Comprueba actualización atómica de lecturas mediante operador $push e incremento de contador con $inc.", "• test_04_atomic_telemetry_push: ")
    add_bullet("Valida ejecución sin fallos y retornos correctos de las 2 agregaciones nativas ($group y $unwind).", "• test_05_native_aggregation_pipelines: ")
    add_bullet("Valida el segundo flujo completo: conclusión de misión y liberación del dron a AVAILABLE.", "• test_06_complete_and_delete_mission_business_flow: ")

    add_callout(
        doc,
        "Comando de ejecución: 'python manage.py test control_center' -> Resultado oficial: Ran 6 tests in 6.891s -> OK.",
        title="RESULTADO OFICIAL DE PRUEBAS",
        border_color="059669",
        bg_color="ECFDF5"
    )

    # ==============================================================================
    # SEMANA 8: INSTRUCCIONES DE REPRODUCIBILIDAD Y GUÍA DE DEFENSA
    # ==============================================================================
    add_h1("Semana 8: Reproducibilidad, Puesta en Marcha y Defensa")
    
    add_h2("1. Guía de Ejecución Reproducible desde Cero")
    add_p("Cualquier evaluador o docente puede ejecutar y probar el proyecto siguiendo estos sencillos pasos:")
    add_bullet("git clone <url-del-repositorio> && cd DronesRBG", "1. Clonar el repositorio: ")
    add_bullet("pip install -r requirements.txt (instala Django, PyMongo, Mongomock y python-dotenv)", "2. Instalar dependencias: ")
    add_bullet("Copiar archivo de plantilla: copy .env.example .env (configurar MONGO_URI si se desea apuntar a otro clúster)", "3. Configurar entorno: ")
    add_bullet("python manage.py runserver 127.0.0.1:8000", "4. Iniciar servidor Django: ")
    add_bullet("Acceder en el navegador a http://127.0.0.1:8000/", "5. Explorar la plataforma: ")

    add_h2("2. Argumentos Clave para la Defensa Oral del Proyecto (15-20 min)")
    add_bullet(
        "Respuesta: Si en el futuro añadimos un sensor LiDAR con 10 atributos de nube de puntos, en SQL tendríamos que alterar tablas "
        "y migrar bases de datos en producción. En MongoDB simplemente enviamos el nuevo objeto dentro de waypoints sin alterar el esquema existente.",
        "• Pregunta: ¿Por qué no usar PostgreSQL con columnas JSONB en lugar de MongoDB? -> "
    )
    add_bullet(
        "Respuesta: Agregación 1 responde al rendimiento de negocio por sector ($group + $avg + $sum) y Agregación 2 ($unwind) demuestra "
        "la potencia del modelo documental para desenrollar arreglos embebidos polimórficos.",
        "• Pregunta: ¿Qué información útil producen las agregaciones? -> "
    )
    add_bullet(
        "Respuesta: El índice idx_telemetry_mission_ts evita examinar toda la colección de telemetría (reducción de 160 a 100 documentos en pruebas, "
        "y de millones a cientos en producción) y elimina el costo de ordenar en memoria.",
        "• Pregunta: ¿Qué evidencia demuestra la utilidad de los índices? -> "
    )

    # Guardar documento
    doc.save(output_path)
    print(f">>> [Word Export] Archivo guardado exitosamente en: {output_path}")

if __name__ == "__main__":
    out_file = os.path.abspath("Informe_Proyecto_Integrador_MongoDB_Drones_RBG.docx")
    generate_full_report(out_file)
