from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import Group, User
from django.views.generic import(
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)
from .forms import CuartelForm, LecturaSensorForm, PredioForm
from .models import Cuartel, LecturaSensor, Predio
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse_lazy


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
        response = super().delete(request, *args, **kwargs)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    def get_template_names(self):
        usuario = self.request.user
        if usuario.groups.filter(name="Administrador").exists():
            return ["dashboard/administrador.html"]
        elif usuario.groups.filter(name="Jefe de cuadrilla").exists():
            return ["dashboard/jefe_cuadrilla.html"]
        elif usuario.groups.filter(name="Trabajador").exists():
            return ["dashboard/trabajador.html"]
        return ["dashboard.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = self.request.user
        if usuario.groups.filter(name="Administrador").exists():
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

        ver_predios = usuario.has_perm(
            "gestor.view_predio"
        )

        ver_cuarteles = usuario.has_perm(
            "gestor.view_cuartel"
        )

        ver_lecturas = usuario.has_perm(
            "gestor.view_lecturasensor"
        )

        ctx["puede_ver_predios"] = ver_predios
        ctx["puede_ver_cuarteles"] = ver_cuarteles
        ctx["puede_ver_lecturas"] = ver_lecturas

        ctx["total_predios"] = (
            Predio.objects.count()
            if ver_predios
            else None
        )

        ctx["total_cuarteles"] = (
            Cuartel.objects.count()
            if ver_cuarteles
            else None
        )

        ctx["total_lecturas"] = (
            LecturaSensor.objects.count()
            if ver_lecturas
            else None
        )

        if ver_lecturas:

            ctx["ultimas_lecturas"] = (
                LecturaSensor.objects
                .select_related("cuartel__predio")
                .order_by("-fecha")[:5]
            )

        else:

            ctx["ultimas_lecturas"] = []

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
