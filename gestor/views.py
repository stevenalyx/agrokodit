from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)
from .forms import (
    ColleraForm,
    CuadrillaForm,
    CuartelForm,
    HuertoForm,
    LaborForm,
    PersonalAgricolaForm,
    PredioForm,
    RegistroJornadaForm,
)
from .models import (
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


class UsuarioPasswordChangeSelfView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "form.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Tu contraseña se actualizó correctamente."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

class AvisoAlertaMixin:
    # muestra el aviso de éxito (sucess_message) después de eliminar un registro
    success_message = ""

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar este registro porque tiene jornadas agrícolas asociadas.",
            )
            return redirect(self.get_success_url())
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class AdministradorPermisoMixin(PermissionRequiredMixin):
    def es_administrador(self):
        usuario = self.request.user
        return usuario.is_superuser or usuario.groups.filter(
            name="Administrador"
        ).exists()

    def has_permission(self):
        return self.es_administrador() or super().has_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["es_administrador"] = self.es_administrador()
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_template_names(self):
        usuario = self.request.user
        if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
            return ["dashboard/administrador.html"]
        elif usuario.groups.filter(name="Jefe de cuadrilla").exists():
            return ["dashboard/jefe_cuadrilla.html"]
        elif usuario.groups.filter(name="Trabajador").exists():
            return ["dashboard/trabajador.html"]
        return ["dashboard.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = self.request.user
        if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
            rol = "Administrador"
        elif usuario.groups.filter(name="Jefe de cuadrilla").exists():
            rol = "Jefe de cuadrilla"
        elif usuario.groups.filter(name="Trabajador").exists():
            rol = "Trabajador"
        else:
            rol = "Sin rol"

        ctx["rol"] = rol
        ctx["usuario"] = usuario

        ctx["es_administrador"] = rol == "Administrador"
        ctx["es_jefe_cuadrilla"] = rol == "Jefe de cuadrilla"
        ctx["es_trabajador"] = rol == "Trabajador"

        jornadas = RegistroJornada.objects.select_related(
            "collera__cuadrilla__jefe__user",
            "collera__trabajador_1__user",
            "collera__trabajador_2__user",
            "cuartel__huerto__predio",
            "labor",
            "validado_por__user",
        )
        jefe = JCuadrilla.objects.filter(user=usuario).first()
        trabajador = Trabajador.objects.filter(user=usuario).first()
        if rol == "Jefe de cuadrilla":
            jornadas = (
                jornadas.filter(collera__cuadrilla__jefe=jefe)
                if jefe
                else jornadas.none()
            )
        elif rol == "Trabajador":
            if trabajador:
                jornadas = jornadas.filter(
                    Q(collera__trabajador_1=trabajador)
                    | Q(collera__trabajador_2=trabajador)
                )
            else:
                jornadas = jornadas.none()
        elif rol != "Administrador":
            jornadas = jornadas.none()

        resumen = jornadas.aggregate(
            kilos=Sum("kilos_producidos"),
            perdidas=Sum("kilos_perdida"),
        )
        ctx["total_jornadas"] = jornadas.count()
        ctx["total_kilos"] = resumen["kilos"] or 0
        ctx["total_perdidas"] = resumen["perdidas"] or 0
        ctx["jornadas_pendientes"] = jornadas.filter(validado=False).count()
        ctx["ultimas_jornadas"] = jornadas.order_by("-fecha", "-id")[:8]

        if rol == "Administrador":
            ctx["total_predios"] = Predio.objects.count()
            ctx["total_huertos"] = Huerto.objects.count()
            ctx["total_cuarteles"] = Cuartel.objects.count()
            ctx["total_cuadrillas"] = Cuadrilla.objects.count()
            ctx["total_colleras"] = Collera.objects.count()
        elif rol == "Jefe de cuadrilla":
            ctx["total_cuadrillas"] = (
                jefe.cuadrillas.count() if jefe else 0
            )
            ctx["total_colleras"] = (
                Collera.objects.filter(cuadrilla__jefe=jefe).count()
                if jefe
                else 0
            )
        elif rol == "Trabajador":
            if trabajador:
                colleras = Collera.objects.filter(
                    Q(trabajador_1=trabajador) | Q(trabajador_2=trabajador)
                )
                ctx["total_colleras"] = colleras.count()
                asistencias = Q(
                    collera__trabajador_1=trabajador,
                    asistencia_trabajador_1=True,
                ) | Q(
                    collera__trabajador_2=trabajador,
                    asistencia_trabajador_2=True,
                )
                ctx["asistencias_personales"] = jornadas.filter(asistencias).count()
            else:
                ctx["total_colleras"] = 0
                ctx["asistencias_personales"] = 0
        else:
            ctx["total_colleras"] = 0

        return ctx


# ---------- Predios ----------
class PredioListView(LoginRequiredMixin, AdministradorPermisoMixin, ListView):
    model = Predio
    permission_required = "gestor.view_predio"
    paginate_by = 10
    template_name = "predio_list.html"


class PredioDetailView(LoginRequiredMixin, AdministradorPermisoMixin, DetailView):
    model = Predio
    permission_required = "gestor.view_predio"
    template_name = "predio_detail.html"
    queryset = Predio.objects.prefetch_related("huertos__cuarteles")


class PredioCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                       SuccessMessageMixin, CreateView):
    model = Predio
    form_class = PredioForm
    permission_required = "gestor.add_predio"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se creó correctamente."
    extra_context = {"titulo": "Nuevo predio"}


class PredioUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                       SuccessMessageMixin, UpdateView):
    model = Predio
    form_class = PredioForm
    permission_required = "gestor.change_predio"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se actualizó correctamente."
    extra_context = {"titulo": "Editar predio"}


class PredioDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                       AvisoAlertaMixin, DeleteView):
    model = Predio
    permission_required = "gestor.delete_predio"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El predio se eliminó."


# ---------- Cuarteles ----------
class CuartelCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
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
        if huerto_id := self.request.GET.get("huerto"):
            initial["huerto"] = huerto_id
        return initial


class CuartelUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                        SuccessMessageMixin, UpdateView):
    model = Cuartel
    form_class = CuartelForm
    permission_required = "gestor.change_cuartel"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El cuartel se actualizó correctamente."
    extra_context = {"titulo": "Editar cuartel"}


class CuartelDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                        AvisoAlertaMixin, DeleteView):
    model = Cuartel
    permission_required = "gestor.delete_cuartel"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El cuartel se eliminó."


class HuertoCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                       SuccessMessageMixin, CreateView):
    model = Huerto
    form_class = HuertoForm
    permission_required = "gestor.add_huerto"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El huerto se creó correctamente."
    extra_context = {"titulo": "Nuevo huerto"}

    def get_initial(self):
        initial = super().get_initial()
        if predio_id := self.request.GET.get("predio"):
            initial["predio"] = predio_id
        return initial


class HuertoUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                       SuccessMessageMixin, UpdateView):
    model = Huerto
    form_class = HuertoForm
    permission_required = "gestor.change_huerto"
    template_name = "form.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El huerto se actualizó correctamente."
    extra_context = {"titulo": "Editar huerto"}


class HuertoDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                       AvisoAlertaMixin, DeleteView):
    model = Huerto
    permission_required = "gestor.delete_huerto"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("predio_list")
    success_message = "El huerto se eliminó."


class CuadrillaListView(LoginRequiredMixin, AdministradorPermisoMixin, ListView):
    model = Cuadrilla
    permission_required = "gestor.view_cuadrilla"
    template_name = "cuadrilla_list.html"
    queryset = Cuadrilla.objects.select_related("jefe__user").prefetch_related(
        "colleras"
    )


class CuadrillaCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                          SuccessMessageMixin, CreateView):
    model = Cuadrilla
    form_class = CuadrillaForm
    permission_required = "gestor.add_cuadrilla"
    template_name = "form.html"
    success_url = reverse_lazy("cuadrilla_list")
    success_message = "La cuadrilla se creó correctamente."
    extra_context = {"titulo": "Nueva cuadrilla"}


class CuadrillaUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                          SuccessMessageMixin, UpdateView):
    model = Cuadrilla
    form_class = CuadrillaForm
    permission_required = "gestor.change_cuadrilla"
    template_name = "form.html"
    success_url = reverse_lazy("cuadrilla_list")
    success_message = "La cuadrilla se actualizó correctamente."
    extra_context = {"titulo": "Editar cuadrilla"}


class CuadrillaDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                          AvisoAlertaMixin, DeleteView):
    model = Cuadrilla
    permission_required = "gestor.delete_cuadrilla"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("cuadrilla_list")
    success_message = "La cuadrilla se eliminó."


class ColleraListView(LoginRequiredMixin, AdministradorPermisoMixin, ListView):
    model = Collera
    permission_required = "gestor.view_collera"
    template_name = "collera_list.html"
    queryset = Collera.objects.select_related(
        "cuadrilla",
        "trabajador_1__user",
        "trabajador_2__user",
    )


class ColleraCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                        SuccessMessageMixin, CreateView):
    model = Collera
    form_class = ColleraForm
    permission_required = "gestor.add_collera"
    template_name = "form.html"
    success_url = reverse_lazy("collera_list")
    success_message = "La collera se creó correctamente."
    extra_context = {"titulo": "Nueva collera"}


class ColleraUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                        SuccessMessageMixin, UpdateView):
    model = Collera
    form_class = ColleraForm
    permission_required = "gestor.change_collera"
    template_name = "form.html"
    success_url = reverse_lazy("collera_list")
    success_message = "La collera se actualizó correctamente."
    extra_context = {"titulo": "Editar collera"}


class ColleraDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                        AvisoAlertaMixin, DeleteView):
    model = Collera
    permission_required = "gestor.delete_collera"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("collera_list")
    success_message = "La collera se eliminó."


class LaborListView(LoginRequiredMixin, AdministradorPermisoMixin, ListView):
    model = Labor
    permission_required = "gestor.view_labor"
    template_name = "labor_list.html"


class LaborCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                      SuccessMessageMixin, CreateView):
    model = Labor
    form_class = LaborForm
    permission_required = "gestor.add_labor"
    template_name = "form.html"
    success_url = reverse_lazy("labor_list")
    success_message = "La labor se creó correctamente."
    extra_context = {"titulo": "Nueva labor"}


class LaborUpdateView(LoginRequiredMixin, AdministradorPermisoMixin,
                      SuccessMessageMixin, UpdateView):
    model = Labor
    form_class = LaborForm
    permission_required = "gestor.change_labor"
    template_name = "form.html"
    success_url = reverse_lazy("labor_list")
    success_message = "La labor se actualizó correctamente."
    extra_context = {"titulo": "Editar labor"}


class LaborDeleteView(LoginRequiredMixin, AdministradorPermisoMixin,
                      AvisoAlertaMixin, DeleteView):
    model = Labor
    permission_required = "gestor.delete_labor"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("labor_list")
    success_message = "La labor se eliminó."


class PersonalAgricolaListView(LoginRequiredMixin, AdministradorPermisoMixin,
                               TemplateView):
    permission_required = "auth.view_user"
    template_name = "personal_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jefes"] = JCuadrilla.objects.select_related("user").all()
        context["trabajadores"] = Trabajador.objects.select_related("user").all()
        return context


class PersonalAgricolaCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                                 SuccessMessageMixin, CreateView):
    form_class = PersonalAgricolaForm
    permission_required = "auth.add_user"
    template_name = "form.html"
    success_url = reverse_lazy("personal_list")
    success_message = "La cuenta y el perfil agrícola se crearon correctamente."
    extra_context = {"titulo": "Agregar personal agrícola"}


def jornadas_visibles_para(usuario):
    queryset = RegistroJornada.objects.select_related(
        "collera__cuadrilla__jefe__user",
        "collera__trabajador_1__user",
        "collera__trabajador_2__user",
        "cuartel__huerto__predio",
        "labor",
        "validado_por__user",
    )
    if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
        return queryset
    if usuario.groups.filter(name="Jefe de cuadrilla").exists():
        return queryset.filter(collera__cuadrilla__jefe__user=usuario)
    if usuario.groups.filter(name="Trabajador").exists():
        return queryset.filter(
            Q(collera__trabajador_1__user=usuario)
            | Q(collera__trabajador_2__user=usuario)
        )
    return queryset.none()


class RegistroJornadaListView(LoginRequiredMixin, AdministradorPermisoMixin, ListView):
    model = RegistroJornada
    permission_required = "gestor.view_registrojornada"
    paginate_by = 15
    template_name = "jornada_list.html"

    def get_queryset(self):
        return jornadas_visibles_para(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        es_jefe = usuario.groups.filter(name="Jefe de cuadrilla").exists()
        context["es_jefe_cuadrilla"] = es_jefe
        context["puede_editar_asistencia"] = (
            usuario.is_superuser
            or usuario.groups.filter(name="Administrador").exists()
            or (es_jefe and usuario.has_perm("gestor.change_registrojornada"))
        )
        return context


class RegistroJornadaCreateView(LoginRequiredMixin, AdministradorPermisoMixin,
                                SuccessMessageMixin, CreateView):
    model = RegistroJornada
    form_class = RegistroJornadaForm
    permission_required = "gestor.add_registrojornada"
    template_name = "form.html"
    success_url = reverse_lazy("jornada_list")
    success_message = "La jornada se registró correctamente."
    extra_context = {"titulo": "Registrar jornada"}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        if form:
            colleras = form.fields["collera"].queryset.select_related(
                "trabajador_1__user", "trabajador_2__user"
            )
            context["colleras_asistencia"] = {
                str(collera.pk): {
                    "trabajador_1": str(collera.trabajador_1),
                    "trabajador_2": str(collera.trabajador_2),
                }
                for collera in colleras
            }
        else:
            context["colleras_asistencia"] = {}
        return context


class RegistroJornadaValidarView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "gestor.change_registrojornada"
    raise_exception = True

    def post(self, request, pk):
        jornada = get_object_or_404(jornadas_visibles_para(request.user), pk=pk)
        jefe = JCuadrilla.objects.filter(user=request.user).first()
        if not jefe or jornada.collera.cuadrilla.jefe_id != jefe.pk:
            raise PermissionDenied
        if jornada.validado:
            messages.warning(request, "Esta jornada ya fue validada.")
        else:
            jornada.validado = True
            jornada.validado_por = jefe
            jornada.fecha_validacion = timezone.now()
            jornada.save(
                update_fields=["validado", "validado_por", "fecha_validacion"]
            )
            messages.success(request, "La jornada fue validada.")
        return redirect("jornada_list")


class RegistroJornadaAsistenciaView(
    LoginRequiredMixin, AdministradorPermisoMixin, View
):
    permission_required = "gestor.change_registrojornada"
    raise_exception = True

    def post(self, request, pk):
        usuario = request.user
        es_administrador = usuario.is_superuser or usuario.groups.filter(
            name="Administrador"
        ).exists()
        jefe = JCuadrilla.objects.filter(user=usuario).first()
        if not es_administrador and not jefe:
            raise PermissionDenied

        jornada = get_object_or_404(jornadas_visibles_para(usuario), pk=pk)
        if jornada.validado:
            messages.error(
                request,
                "La asistencia no se puede modificar porque la jornada ya fue validada.",
            )
            return redirect("jornada_list")

        jornada.asistencia_trabajador_1 = (
            request.POST.get("asistencia_trabajador_1") == "on"
        )
        jornada.asistencia_trabajador_2 = (
            request.POST.get("asistencia_trabajador_2") == "on"
        )
        jornada.save(
            update_fields=["asistencia_trabajador_1", "asistencia_trabajador_2"]
        )
        messages.success(request, "La asistencia de la jornada se actualizó.")
        return redirect("jornada_list")

# crear roles de administrador, jefe cuadrilla y trabajador
# Los permisos se asignan de la siguiente manera:
# Administrador: crea usuarios y roles, configura predios, huertos y cuarteles, forma cuadrillas y colleras y accede a todos los reportes.
# Jefe de cuadrilla: visualiza sus colleras y trabajadores, registra o valida asistencia, registra labores y producción y revisa el rendimiento de su cuadriila.
# Trabajador: consulta su asistencia, ve sus labores y cuartel asignado, consulta su producción personal y revisa la producción de su collera.

class RolListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = "auth.view_group"
    paginate_by = 10
    template_name = "roles.html"

class RolCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                   SuccessMessageMixin, CreateView):
    model = Group
    fields = ["name", "permissions"]
    permission_required = "auth.add_group"
    template_name = "form.html"
    success_url = reverse_lazy("rol_list")
    success_message = "El rol se creó correctamente."
    extra_context = {"titulo": "Nuevo rol"}

class RolUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                   SuccessMessageMixin, UpdateView):
    model = Group
    fields = ["name", "permissions"]
    permission_required = "auth.change_group"
    template_name = "form.html"
    success_url = reverse_lazy("rol_list")
    success_message = "El rol se actualizó correctamente."
    extra_context = {"titulo": "Editar rol"}

    def get_success_url(self):
        return reverse_lazy("rol_list")

class RolDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                   AvisoAlertaMixin, DeleteView):
    model = Group
    permission_required = "auth.delete_group"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("rol_list")
    success_message = "El rol se eliminó."

    def get_success_url(self):
        # Redirige a la lista de roles después de eliminar un rol
        return reverse_lazy("rol_list")

class RolDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Group
    permission_required = "auth.view_group"
    template_name = "rol_detail.html"

class UsuarioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    permission_required = "auth.view_user"
    paginate_by = 10
    template_name = "usuario_list.html"

class UsuarioCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                   SuccessMessageMixin, CreateView):
    model = User
    fields = ["username", "email", "password", "groups"]
    permission_required = "auth.add_user"
    template_name = "form.html"
    success_url = reverse_lazy("usuario_list")
    success_message = "El usuario se creó correctamente."
    extra_context = {"titulo": "Nuevo usuario"}

class UsuarioUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                   SuccessMessageMixin, UpdateView):
    model = User
    fields = ["username", "email", "password", "groups"]
    permission_required = "auth.change_user"
    template_name = "form.html"
    success_url = reverse_lazy("usuario_list")
    success_message = "El usuario se actualizó correctamente."
    extra_context = {"titulo": "Editar usuario"}

class UsuarioDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                   AvisoAlertaMixin, DeleteView):
    model = User
    permission_required = "auth.delete_user"
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("usuario_list")
    success_message = "El usuario se eliminó."

    def get_success_url(self):
            # Redirige a la lista de usuarios después de eliminar un usuario
            return reverse_lazy("usuario_list")

class UsuarioDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    permission_required = "auth.view_user"
    template_name = "usuario_detail.html"

class UsuarioPasswordChangeView(LoginRequiredMixin, PermissionRequiredMixin,
                   SuccessMessageMixin, UpdateView):
    model = User
    fields = ["password"]
    permission_required = "auth.change_user"
    template_name = "form.html"
    success_url = reverse_lazy("usuario_list")
    success_message = "La contraseña del usuario se actualizó correctamente."
    extra_context = {"titulo": "Cambiar contraseña de usuario"}

    def form_valid(self, form):
        # Cambia la contraseña del usuario
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        return super().form_valid(form)

class UsuarioPasswordChangeSelfView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["password"]
    template_name = "form.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Tu contraseña se actualizó correctamente."
    extra_context = {"titulo": "Cambiar tu contraseña"}

    def get_object(self, queryset=None):
        # Devuelve el usuario actual
        return self.request.user

    def form_valid(self, form):
        # Cambia la contraseña del usuario actual
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        return super().form_valid(form)

class UsuarioProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "usuario_profile.html"

    def get_object(self, queryset=None):
        # Devuelve el usuario actual
        return self.request.user

class UsuarioProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["username", "email"]
    template_name = "form.html"
    success_url = reverse_lazy("usuario_profile")
    success_message = "Tu perfil se actualizó correctamente."
    extra_context = {"titulo": "Editar tu perfil"}

    def get_object(self, queryset=None):
        # Devuelve el usuario actual
        return self.request.user

class UsuarioProfilePasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["password"]
    template_name = "form.html"
    success_url = reverse_lazy("usuario_profile")
    success_message = "Tu contraseña se actualizó correctamente."
    extra_context = {"titulo": "Cambiar tu contraseña"}

    def get_object(self, queryset=None):
        # Devuelve el usuario actual
        return self.request.user

    def form_valid(self, form):
        # Cambia la contraseña del usuario actual
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        return super().form_valid(form)

class UsuarioProfileDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = User
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Tu cuenta se eliminó correctamente."
    extra_context = {"titulo": "Eliminar tu cuenta"}

    def get_object(self, queryset=None):
        # Devuelve el usuario actual
        return self.request.user

class UsuarioProfileDeleteConfirmView(LoginRequiredMixin, TemplateView):
    template_name = "usuario_profile_delete_confirm.html"
