from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import CuartelForm, LecturaSensorForm, PredioForm
from .models import Cuartel, LecturaSensor, Predio


class AvisoAlertaMixin:
    # muestra el aviso de éxito (sucess_message) después de eliminar un registro
    success_message = ""

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario=self.request.user
        ver_predios = usuario.has_perm("gestor.view_predio")
        ver_cuarteles = usuario.has_perm("gestor.view_cuartel")
        ver_lecturas = usuario.has_perm("gestor.view_lecturasensor")

        ctx["total_predios"] = Predio.objects.count() if ver_predios else None
        ctx["total_cuarteles"] = Cuartel.objects.count() if ver_cuarteles else None
        ctx["total_lecturas"] = LecturaSensor.objects.count() if ver_lecturas else None

        ctx["ultimas_lecturas"] = (
            LecturaSensor.objects.select_related("cuartel__predio")
            .order_by("-fecha")[:5]
        )
        return ctx


# ---------- Predios ----------
class PredioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Predio
    permission_required = "gestor.view_predio"
    paginate_by = 10
    template_name = "predio_list.html"


class PredioDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Predio
    permission_required = "gestor.view_predio"
    template_name = "predio_detail.html"


class PredioCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                       SuccessMessageMixin, CreateView):
    model = Predio
    form_class = PredioForm
    permission_required = "gestor.add_predio"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se creó correctamente."
    extra_context = {"titulo": "Nuevo predio"}


class PredioUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                       SuccessMessageMixin, UpdateView):
    model = Predio
    form_class = PredioForm
    permission_required = "gestor.change_predio"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se actualizó correctamente."
    extra_context = {"titulo": "Editar predio"}


class PredioDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                       AvisoAlertaMixin, DeleteView):
    model = Predio
    permission_required = "gestor.delete_predio"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se eliminó."


# ---------- Cuarteles ----------
class CuartelCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                        SuccessMessageMixin, CreateView):
    model = Cuartel
    form_class = CuartelForm
    permission_required = "gestor.add_cuartel"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El cuartel se creó correctamente."
    extra_context = {"titulo": "Nuevo cuartel"}

    def get_initial(self):
        initial = super().get_initial()
        if predio_id := self.request.GET.get("predio"):
            initial["predio"] = predio_id
        return initial


class CuartelUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                        SuccessMessageMixin, UpdateView):
    model = Cuartel
    form_class = CuartelForm
    permission_required = "gestor.change_cuartel"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El cuartel se actualizó correctamente."
    extra_context = {"titulo": "Editar cuartel"}


class CuartelDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                        AvisoAlertaMixin, DeleteView):
    model = Cuartel
    permission_required = "gestor.delete_cuartel"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El cuartel se eliminó."


# ---------- Lecturas ----------
class LecturaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LecturaSensor
    permission_required = "gestor.view_lecturasensor"
    paginate_by = 15
    template_name = "lectura_list.html"

    def _cuartel_filtrado(self):
        valor = self.request.GET.get("cuartel", "")
        return valor if valor.isdigit() else ""

    def get_queryset(self):
        queryset = LecturaSensor.objects.select_related("cuartel__predio").order_by("-fecha")
        if cuartel_id := self._cuartel_filtrado():
            queryset = queryset.filter(cuartel_id=cuartel_id)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cuartel = self._cuartel_filtrado()
        ctx["cuarteles"] = Cuartel.objects.select_related("predio")
        ctx["cuartel_sel"] = cuartel
        ctx["extra_query"] = f"&cuartel={cuartel}" if cuartel else ""
        return ctx


class LecturaCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                        SuccessMessageMixin, CreateView):
    
    model = LecturaSensor
    form_class = LecturaSensorForm
    permission_required = "gestor.add_lecturasensor"
    template_name = "form.html"
    success_url = reverse_lazy("lectura_list")
    success_message = "La lectura se registró correctamente."
    extra_context = {"titulo": "Registrar lectura de sensor"}