"""
URL configuration for control_center app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Web UI Views
    path('', views.dashboard_view, name='dashboard'),
    path('operator/', views.operator_view, name='operator'),
    path('commander/', views.commander_view, name='commander'),
    path('architecture/', views.architecture_view, name='architecture'),

    # REST API Endpoints
    path('api/status/', views.api_status, name='api_status'),
    path('api/drones/', views.api_drones_list, name='api_drones_list'),
    path('api/drones/<str:drone_id>/missions/', views.api_drone_missions_history, name='api_drone_missions_history'),
    path('api/missions/', views.api_missions_list_create, name='api_missions_list_create'),
    path('api/missions/<str:mission_id>/', views.api_mission_detail, name='api_mission_detail'),
    path('api/missions/<str:mission_id>/complete/', views.api_mission_complete, name='api_mission_complete'),
    path('api/missions/<str:mission_id>/delete/', views.api_mission_delete, name='api_mission_delete'),
    path('api/missions/<str:mission_id>/telemetry/', views.api_mission_telemetry, name='api_mission_telemetry'),
    path('api/missions/<str:mission_id>/telemetria-document/', views.api_mission_telemetria_doc, name='api_mission_telemetria_doc'),
    path('api/missions/<str:mission_id>/audit/', views.api_mission_audit, name='api_mission_audit'),
    path('api/missions/<str:mission_id>/simulate-step/', views.api_simulate_step, name='api_simulate_step'),
    path('api/analytics/aggregations/', views.api_analytics_aggregations, name='api_analytics_aggregations'),
    path('api/reset-seed/', views.api_reset_seed, name='api_reset_seed'),
]
