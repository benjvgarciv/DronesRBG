# Drones RBG - Centro de Control de Telemetría y Misiones con Drones

[![Python 3.14+](https://img.shields.io/badge/Python-3.14+-000000?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-000000?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![MongoDB PyMongo](https://img.shields.io/badge/MongoDB-PyMongo_Driver-000000?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Leaflet](https://img.shields.io/badge/Maps-Leaflet_Táctico-000000?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com)
[![Chart.js](https://img.shields.io/badge/Telemetry-Chart.js-000000?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)

---

## 1. Datos Generales del Proyecto

* **Nombre del Proyecto:** Drones RBG - Centro de Control de Telemetría y Misiones con Drones
* **Plataforma / Arquitectura:** Aplicación Web (Backend: Python + Django / Base de Datos: MongoDB mediante PyMongo)
* **Integrantes del Equipo (RBG):**
  * 👤 **Rodrigo Tapia**
  * 👤 **Benjamin Garcia**
  * 👤 **Gustavo Jaramillo**

---

## 2. Planteamiento del Problema y Justificación Técnica (MongoDB vs SQL)

En los sectores **industrial, agrícola y de seguridad**, la operación de flotas de aeronaves no tripuladas (UAVs / drones) requiere:
1. **Planificar rutas complejas de vuelo (misiones)** con puntos de navegación dinámicos.
2. **Monitorear en tiempo real variables de salud, telemetría y geolocalización** de los vehículos.

### ¿Por qué las bases de datos relacionales tradicionales (SQL) enfrentan severas limitaciones?

1. **Atributos de ruta heterogéneos:**
   * Cada punto de navegación (*waypoint*) exige tareas de naturaleza completamente distinta:
     * **Captura fotográfica:** Parámetros de cámara RGB 48MP, sensibilidad ISO, tiempo de obturación, apertura focal, ángulo del gimbal e identificación de estructura objetivo.
     * **Escaneo térmico radiométrico:** Paleta cromática FLIR (IronBow/Rainbow), emisividad superficial, umbral de alarma en °C, captura de stream infrarrojo.
     * **Hover o giro panorámico 360°:** Tiempo estacionario de espera, velocidad angular de rotación (°/s), porcentaje de solapamiento.
     * **Adquisición multiespectral NDVI:** Bandas espectrales (Green, Red, RedEdge, NIR) para índice de vigor vegetativo.
     * **Aterrizaje y RTH:** Detección de plataforma de precisión mediante sensores ópticos RTK inferiores.
   * *Limitación en SQL:* Obligaría a crear una tabla desnormalizada con docenas de columnas donde el **90% son valores NULL**, o diseñar un esquema relacional complejo con múltiples tablas puente que degradan severamente el rendimiento con costosos `JOINs`.
   * *Solución en MongoDB:* Modelo documental flexible y polimórfico en BSON. Cada waypoint se almacena como un subdocumento embebido en la colección `missions`, conteniendo exclusivamente los parámetros necesarios para su tarea sin rigidez de esquema.

2. **Volumen de telemetría en serie temporal:**
   * Las ráfagas continuas de datos durante el vuelo (coordenadas GPS, altitud barométrica, velocidad terrestre, nivel de batería, voltaje, amperaje, temperatura de motores y calidad de señal) generan escrituras constantes de alta frecuencia con sellos de tiempo (*timestamps*).
   * *Limitación en SQL:* Los motores relacionales tradicionales con bloqueos de tabla/página y comprobación estricta de llaves foráneas sufren cuellos de botella ante escrituras de ráfagas masivas concurrentes.
   * *Solución en MongoDB:* Motor optimizado para ingestión de alta velocidad con PyMongo (`insert_one` / `insert_many`), indexación BSON sobre `{mission_id: 1, timestamp: 1}` y agregaciones nativas (Aggregation Pipeline) para análisis de series temporales.

---

## 3. Usuarios Principales y Casos de Uso Implementados

### 🎯 Operador de Vuelo (`/operator/`)
* **Diseño táctico interactivo:** Mapa satelital oscuro en Leaflet que permite situar waypoints mediante clics directos.
* **Configuración de tareas heterogéneas:** Asignación dinámica de parámetros para fotografía, escaneo térmico FLIR, panorámica 360°, multiespectral o aterrizaje.
* **Cálculo automático de ruta:** Distancia total en metros, tiempo estimado de vuelo y consumo de batería proyectado.
* **Ejecución y Monitoreo en Vivo (HUD Cockpit):**
  * Instrumento de horizonte artificial con giroscopio (rotación e inclinación Roll/Pitch visual).
  * Velocímetro terrestre digital (km/h y m/s) y altímetro relativo.
  * Gauge dinámico de batería restante con alerta por código de color.
  * Indicador de satélites GPS, temperatura de motor y potencia instantánea.
  * Transmisión y registro de ráfagas en vivo directamente en MongoDB.

### 📊 Comandante de Flota / Auditor (`/commander/`)
* **Historial Completo de Misiones:** Filtros y selección de misiones con estados `COMPLETED`, `IN_PROGRESS` y `PLANNED`.
* **Evaluación de Consumo de Energía según Condiciones de Vuelo:**
  * Gráfico multieje interactivo (Chart.js): **Batería (%) vs. Velocidad (km/h) y Altitud (m)** a lo largo del tiempo.
  * Gráfico de diagnóstico: **Potencia Instantánea (Watts) vs. Temperatura del Motor (°C)**.
* **Métricas de Rendimiento por Dron:** Horas de vuelo totales, tasa de consumo energético por kilómetro recorrido (`%/km`), estado de salud del hardware y horas acumuladas.
* **Inspección de Documento BSON Crudo:** Visor con resaltado de sintaxis JSON/BSON del documento recuperado con `db.missions.find_one()` y `db.telemetry.find()`, con botón de copiado rápido para demostración académica.

### 📑 Módulo de Arquitectura & Defensa del Proyecto (`/architecture/`)
* Documentación detallada del proyecto, ficha técnica del equipo y comparación lado a lado del modelo relacional SQL vs modelo documental MongoDB BSON.

---

## 4. Estructura del Proyecto

```
DronesRBG/
├── config/                     # Configuración principal de Django
│   ├── settings.py             # Configuración de PyMongo, static, templates y apps
│   ├── urls.py                 # Enrutamiento raíz
│   └── wsgi.py
├── control_center/             # Aplicación principal de Centro de Control
│   ├── db_client.py            # Cliente PyMongo con detección y fallback mongomock
│   ├── services.py             # Simulador de telemetría y algoritmos de auditoría
│   ├── views.py                # Vistas web y API REST JSON
│   └── urls.py                 # Rutas (/operator/, /commander/, /api/...)
├── static/
│   ├── css/
│   │   └── main.css            # Sistema de diseño aeroespacial oscuro HUD
│   ├── js/
│   │   ├── main.js             # Reloj aeroespacial UTC/Local y heartbeat MongoDB
│   │   ├── operator.js         # Lógica de mapa, waypoints y cabina HUD
│   │   └── commander.js        # Gráficas Chart.js de telemetría y visor BSON
│   └── images/
│       └── hero_drone.jpg      # Fotografía de alta resolución de misión táctica
├── templates/
│   ├── base.html               # Plantilla maestra con navbar, estado PyMongo y equipo
│   ├── dashboard.html          # Panel principal con métricas KPI y flota
│   ├── operator.html           # Centro del Operador de Vuelo
│   ├── commander.html          # Centro del Comandante de Flota / Auditor
│   └── architecture.html       # Comparativa técnica SQL vs MongoDB
└── manage.py
```

---

## 5. Puesta en Marcha y Reproducibilidad

### Requisitos Previos
* **Python 3.10+** (verificado en Python 3.13 / 3.14)
* **MongoDB** (Atlas en la nube o MongoDB Local `mongodb://localhost:27017/drones_rbg` con fallback a `mongomock`).

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### Configuración de Variables de Entorno (.env)
Copiar la plantilla de ejemplo y configurar las credenciales de conexión:
```bash
cp .env.example .env
```
Contenido de `.env`:
```env
DEBUG=True
SECRET_KEY=django-insecure-d()9%_1v^926969_o9k+ju+p8rfsh-cp0mxj_qan636pz6=1_z
MONGO_URI=mongodb+srv://<usuario>:<password>@cluster0.mongodb.net/drones_rbg?retryWrites=true&w=majority
MONGO_DB_NAME=drones_rbg
```

### Carga Inicial de Datos de Prueba (seed_database)
El sistema incluye una base de datos de demostración con aeronaves industriales, misiones con waypoints heterogéneos y series temporales de telemetría:
* **Automática:** Al iniciar el servidor y abrir el Tablero (`/`), si las colecciones están vacías se pueblan automáticamente.
* **Desde la Interfaz Web:** Puedes pulsar el botón **"Poblar Datos de Prueba"** en el panel de Diagnóstico del Servidor en el Tablero principal.
* **Desde Terminal (Django Shell):**
  ```bash
  python manage.py shell -c "from control_center.db_client import seed_database; seed_database(force=True)"
  ```
* **Vía Script mongosh Nativo (Opcional):**
  ```bash
  mongosh drones_rbg mongo_setup.js
  ```

### Ejecutar el Servidor
```bash
python manage.py runserver 127.0.0.1:8000
```
Acceder en el navegador a: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 6. Pruebas Automatizadas y Benchmark de Rendimiento

### Ejecución de Pruebas Unitarias (Suite de 6 Tests)
```bash
python manage.py test control_center
```
Valida conectividad, unicidad de aeronaves, inserciones de waypoints, actualizaciones atómicas con `$push`, pipelines de agregación y el flujo de cierre/eliminación de misiones.

### Benchmark de Rendimiento de Índices (`explain`)
```bash
python benchmark_explain.py
```
Ejecuta `explain("executionStats")` sobre la colección `telemetry` comparando el uso del índice `idx_telemetry_mission_ts` (`IXSCAN`) frente a un escaneo completo (`COLLSCAN`), generando el reporte técnico `EXPLAIN_ANALYSIS.md`.

---

## 7. Diccionario de Datos de Colecciones MongoDB

1. **`drones`:** Aeronaves de la flota.
   * `drone_id` (String, único): Identificador táctico (ej. `DRN-RBG-01`).
   * `name` (String): Nombre operativo.
   * `model` (String): Modelo industrial / chasis.
   * `status` (String enum): `AVAILABLE`, `IN_MISSION`, `MAINTENANCE`.
   * `battery_level` (Double/Int): Nivel de carga (0-100%).
   * `payload_types` (Array de Strings): Sensores instalados (RGB, FLIR, LiDAR, NDVI, etc.).
   * `operator_assigned` (String): Piloto responsable.
   * `total_flight_hours` (Double): Horas acumuladas de vuelo.

2. **`missions`:** Rutas de navegación con waypoints polimórficos embebidos.
   * `mission_id` (String, único): Código de operación (ej. `MSN-2026-001`).
   * `name` (String): Nombre de la misión.
   * `sector` (String enum): `Industrial`, `Agrícola`, `Seguridad`.
   * `assigned_drone_id` (String): Referencia al dron (Relación 1:N).
   * `status` (String enum): `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `ABORTED`.
   * `waypoints` (Array embebido): Subdocumentos con atributos dinámicos según la tarea (`PHOTO_CAPTURE`, `THERMAL_SCAN`, `MULTISPECTRAL_SCAN`, etc.).

3. **`telemetria_misiones`:** Registro consolidado con relación 1:1 con misiones.
   * `mission_id` (String, único): Código de la misión vinculada.
   * `drone_id` (String): Dron ejecutor.
   * `total_readings` (Int): Contador atómico actualizado con `$inc`.
   * `lecturas` (Array embebido): Lecturas históricas insertadas con `$push`.

4. **`telemetry`:** Serie temporal append-only para streaming de alta frecuencia (10 Hz).
   * `mission_id` (String), `drone_id` (String), `timestamp` (Date).
   * `gps`: Subdocumento `{ lat, lng, altitude_m, satellites }`.
   * `flight_dynamics`: Subdocumento `{ speed_kmh, pitch_deg, roll_deg, yaw_deg }`.
   * `power`: Subdocumento `{ battery_pct, voltage_v, power_w }`.
   * `diagnostics`: Subdocumento `{ motor_temp_c, esc_temp_c, sensor_health }`.

---

## 8. Consultas de Agregación Nativas (Aggregation Pipeline)

* **Agregación 1 (Auditoría por Sector):**
  Agrupa misiones por `sector`, calculando tasa de completación, distancia media, consumo de batería y número de drones únicos mediante `$group`, `$project`, `$round` y `$sort`.
* **Agregación 2 (Demanda de Tareas de Sensores):**
  Aprovecha `$unwind` para desenrollar el arreglo embebido `waypoints` y clasificar la frecuencia y altitud/velocidad promedio por tipo de sensor/tarea en toda la flota.

---

## 9. Endpoints de la API REST (PyMongo Directo)

* `GET /api/status/` — Estado de conexión a MongoDB, motor activo y conteo de documentos.
* `GET /api/drones/` — Listado de aeronaves en MongoDB.
* `POST /api/drones/` — Registro de nueva aeronave con validación BSON.
* `GET /api/drones/<id>/missions/` — Historial de misiones por dron (Relación 1:N).
* `GET /api/missions/?sector=...&status=...` — Listado de misiones con filtros dinámicos.
* `POST /api/missions/` — Creación de misión con waypoints heterogéneos.
* `POST /api/missions/<id>/complete/` — Concluir/aprobar misión y liberar aeronave a `AVAILABLE`.
* `POST /api/missions/<id>/delete/` — Eliminar permanentemente misión y telemetría en MongoDB.
* `GET /api/missions/<id>/audit/` — Análisis forense y métricas de consumo para Chart.js.
* `POST /api/missions/<id>/simulate-step/` — Ingesta atómica de telemetría simulada a MongoDB.
* `GET /api/analytics/aggregations/` — Ejecución de las 2 consultas de agregación nativas.
* `POST /api/reset-seed/` — Reinicialización de colecciones con datos de prueba industriales.

---

Desarrollado para el proyecto **Drones RBG** por **Rodrigo Tapia**, **Benjamin Garcia** y **Gustavo Jaramillo**.
