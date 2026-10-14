from django.contrib import admin

from .models import Cuartel, LecturaSensor, Predio

# Mensajes (textos) que se muestran en la interfaz de administración para cada modelo.
admin.site.site_header = "Administración de AgroKODIT"
admin.site.site_title = "AgroKODIT"
admin.site.index_title = "Panel de administración"

class CuartelInline(admin.TabularInline):
    model = Cuartel
    extra = 0


@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "superficie_hectareas")
    search_fields = ("nombre", "ubicacion")
    inlines = [CuartelInline]


@admin.register(Cuartel)
class CuartelAdmin(admin.ModelAdmin):
    list_display = ("nombre", "predio")
    list_filter = ("predio",)
    search_fields = ("nombre",)


@admin.register(LecturaSensor)
class LecturaSensorAdmin(admin.ModelAdmin):
    list_display = ("cuartel", "fecha")
    list_filter = ("cuartel__predio", "cuartel")
    date_hierarchy = "fecha"