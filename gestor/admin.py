from django.contrib import admin

from .models import (
    Administrador,
    Collera,
    Cuadrilla,
    Cuartel,
    Huerto,
    JCuadrilla,
    Labor,
    Predio,
    RegistroJornada,
    Trabajador,
)

admin.site.site_header = "Administración de AgroKODIT"
admin.site.site_title = "AgroKODIT"
admin.site.index_title = "Panel de administración"


class CuartelInline(admin.TabularInline):
    model = Cuartel
    extra = 0


class HuertoInline(admin.TabularInline):
    model = Huerto
    extra = 0


@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "superficie_hectareas")
    search_fields = ("nombre", "ubicacion")
    inlines = [HuertoInline]


@admin.register(Huerto)
class HuertoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "predio")
    list_filter = ("predio",)
    search_fields = ("nombre", "predio__nombre")
    inlines = [CuartelInline]


@admin.register(Cuartel)
class CuartelAdmin(admin.ModelAdmin):
    list_display = ("nombre", "huerto", "superficie_hectareas")
    list_filter = ("huerto__predio", "huerto")
    search_fields = ("nombre", "huerto__nombre", "huerto__predio__nombre")


@admin.register(Cuadrilla)
class CuadrillaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "jefe")
    search_fields = ("nombre", "jefe__user__username")


@admin.register(Collera)
class ColleraAdmin(admin.ModelAdmin):
    list_display = ("__str__", "cuadrilla", "trabajador_1", "trabajador_2")
    list_filter = ("cuadrilla",)
    search_fields = (
        "trabajador_1__user__username",
        "trabajador_2__user__username",
    )


@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre",)


@admin.register(RegistroJornada)
class RegistroJornadaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "collera",
        "cuartel",
        "labor",
        "kilos_producidos",
        "calidad",
        "validado",
    )
    list_filter = ("fecha", "calidad", "validado", "cuartel__huerto__predio")
    search_fields = ("collera__trabajador_1__user__username", "labor__nombre")
    date_hierarchy = "fecha"
    readonly_fields = ("validado_por", "fecha_validacion")


admin.site.register((Administrador, Trabajador, JCuadrilla))
