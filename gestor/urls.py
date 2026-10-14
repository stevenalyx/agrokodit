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

    # cuarteles
    path("cuarteles/nuevo/", views.CuartelCreateView.as_view(), name="cuartel_create"),
    path("cuarteles/<int:pk>/editar/", views.CuartelUpdateView.as_view(), name="cuartel_update"),
    path("cuarteles/<int:pk>/eliminar/", views.CuartelDeleteView.as_view(), name="cuartel_delete"),

    # lecturas
    path("lecturas/", views.LecturaListView.as_view(), name="lectura_list"),
    path("lecturas/nueva/", views.LecturaCreateView.as_view(), name="lectura_create"),
]