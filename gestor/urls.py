from django.urls import path
from . import views

urlpatterns = [
    # inicio
    path("", views.DashboardView.as_view(), name="dashboard"),

    # predios
    path("predios/", views.PredioListView.as_view(), name="predio_list"),
    path("predios/nuevo/", views.PredioCreateView.as_view(), name="predio_create"),
    path("predios/<int:pk>/", views.PredioDetailView.as_view(), name="predio_detail"),
    path("predios/<int:pk>/editar/", views.PredioUpdateView.as_view(), name="predio_update"),
    path("predios/<int:pk>/eliminar/", views.PredioDeleteView.as_view(), name="predio_delete"),

    # huertos
    path("huertos/nuevo/", views.HuertoCreateView.as_view(), name="huerto_create"),
    path("huertos/<int:pk>/editar/", views.HuertoUpdateView.as_view(), name="huerto_update"),
    path("huertos/<int:pk>/eliminar/", views.HuertoDeleteView.as_view(), name="huerto_delete"),

    # cuarteles
    path("cuarteles/nuevo/", views.CuartelCreateView.as_view(), name="cuartel_create"),
    path("cuarteles/<int:pk>/editar/", views.CuartelUpdateView.as_view(), name="cuartel_update"),
    path("cuarteles/<int:pk>/eliminar/", views.CuartelDeleteView.as_view(), name="cuartel_delete"),

    # equipos, colleras y labores
    path("cuadrillas/", views.CuadrillaListView.as_view(), name="cuadrilla_list"),
    path("cuadrillas/nueva/", views.CuadrillaCreateView.as_view(), name="cuadrilla_create"),
    path("cuadrillas/<int:pk>/editar/", views.CuadrillaUpdateView.as_view(), name="cuadrilla_update"),
    path("cuadrillas/<int:pk>/eliminar/", views.CuadrillaDeleteView.as_view(), name="cuadrilla_delete"),
    path("colleras/", views.ColleraListView.as_view(), name="collera_list"),
    path("colleras/nueva/", views.ColleraCreateView.as_view(), name="collera_create"),
    path("colleras/<int:pk>/editar/", views.ColleraUpdateView.as_view(), name="collera_update"),
    path("colleras/<int:pk>/eliminar/", views.ColleraDeleteView.as_view(), name="collera_delete"),
    path("labores/", views.LaborListView.as_view(), name="labor_list"),
    path("labores/nueva/", views.LaborCreateView.as_view(), name="labor_create"),
    path("labores/<int:pk>/editar/", views.LaborUpdateView.as_view(), name="labor_update"),
    path("labores/<int:pk>/eliminar/", views.LaborDeleteView.as_view(), name="labor_delete"),
    path("personal/", views.PersonalAgricolaListView.as_view(), name="personal_list"),
    path("personal/nuevo/", views.PersonalAgricolaCreateView.as_view(), name="personal_create"),

    # jornadas
    path("jornadas/", views.RegistroJornadaListView.as_view(), name="jornada_list"),
    path("jornadas/nueva/", views.RegistroJornadaCreateView.as_view(), name="jornada_create"),
    path(
        "jornadas/<int:pk>/validar/",
        views.RegistroJornadaValidarView.as_view(),
        name="jornada_validar",
    ),
    path(
        "jornadas/<int:pk>/asistencia/",
        views.RegistroJornadaAsistenciaView.as_view(),
        name="jornada_asistencia",
    ),

    # roles
    path("roles/", views.RolListView.as_view(), name="rol_list"),
    # usuarios
    path("usuarios/", views.UsuarioListView.as_view(), name="usuario_list"),
]
