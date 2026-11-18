from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group, Permission, User
from django.db import transaction
from django.db.models import TextChoices

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


class BootstrapAccesibleMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            clase = "form-select" if isinstance(widget, forms.Select) else "form-control"
            actuales = widget.attrs.get("class", "")

            ids = []
            if field.help_text:
                ids.append(f"id_{name}_help")
            if self.is_bound and name in self.errors:
                ids.append(f"id_{name}_error")
                widget.attrs["aria-invalid"] = "true"
                clase += " is-invalid"
            if ids:
                widget.attrs["aria-describedby"] = " ".join(ids)
            if field.required:
                widget.attrs["aria-required"] = "true"

            widget.attrs["class"] = f"{actuales} {clase}".strip()


class LoginForm(BootstrapAccesibleMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Ingresa tú nombre de usuario"
        self.fields["password"].label = "Ingresa tú contraseña"


class PredioForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Predio
        fields = ["nombre", "ubicacion", "superficie_hectareas"]
        labels = {
            "nombre": "Nombre del predio",
            "ubicacion": "Ubicación",
            "superficie_hectareas": "Superficie (hectáreas)",
        }


class HuertoForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Huerto
        fields = ["predio", "nombre"]
        labels = {
            "predio": "Predio al que pertenece",
            "nombre": "Nombre del huerto",
        }


class CuartelForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Cuartel
        fields = ["huerto", "nombre", "superficie_hectareas"]
        labels = {
            "huerto": "Huerto al que pertenece",
            "nombre": "Nombre del cuartel",
            "superficie_hectareas": "Superficie (hectáreas)",
        }


class CuadrillaForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Cuadrilla
        fields = ["nombre", "jefe"]
        labels = {
            "nombre": "Nombre de la cuadrilla",
            "jefe": "Jefe de cuadrilla",
        }


class ColleraForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Collera
        fields = ["cuadrilla", "trabajador_1", "trabajador_2"]
        labels = {
            "cuadrilla": "Cuadrilla",
            "trabajador_1": "Trabajador 1",
            "trabajador_2": "Trabajador 2",
        }


class LaborForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Labor
        fields = ["nombre", "descripcion", "activa"]
        labels = {
            "nombre": "Nombre de la labor",
            "descripcion": "Descripción",
            "activa": "Labor activa",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }


class PersonalAgricolaForm(BootstrapAccesibleMixin, UserCreationForm):
    class Rol(TextChoices):
        TRABAJADOR = "Trabajador", "Trabajador"
        JEFE_CUADRILLA = "Jefe de cuadrilla", "Jefe de cuadrilla"

    rol = forms.ChoiceField(
        choices=Rol.choices,
        label="Rol agrícola",
        help_text="Se creará el perfil de trabajador o jefe de cuadrilla.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if not commit:
            return user

        user.save()
        rol = self.cleaned_data["rol"]
        grupo, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)
        if rol == self.Rol.JEFE_CUADRILLA:
            JCuadrilla.objects.create(user=user, grupo=grupo)
            permisos = [
                "view_registrojornada",
                "add_registrojornada",
                "change_registrojornada",
                "view_predio",
            ]
        else:
            Trabajador.objects.create(user=user, grupo=grupo)
            permisos = ["view_registrojornada"]
        grupo.permissions.add(
            *Permission.objects.filter(
                content_type__app_label="gestor",
                codename__in=permisos,
            )
        )
        return user


class RegistroJornadaForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = RegistroJornada
        fields = [
            "fecha",
            "collera",
            "cuartel",
            "labor",
            "asistencia_trabajador_1",
            "asistencia_trabajador_2",
            "kilos_producidos",
            "calidad",
            "kilos_perdida",
            "observaciones",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "fecha": "Fecha de la jornada",
            "collera": "Collera",
            "cuartel": "Cuartel",
            "labor": "Labor realizada",
            "kilos_producidos": "Kilos producidos",
            "calidad": "Calidad",
            "observaciones": "Observaciones",
        }
        help_texts = {
            "kilos_producidos": "Producción total de la collera para esta jornada.",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not (
            user.is_superuser or user.groups.filter(name="Administrador").exists()
        ):
            jefe = JCuadrilla.objects.filter(user=user).first()
            if jefe is None:
                self.fields["collera"].queryset = Collera.objects.none()
            else:
                self.fields["collera"].queryset = Collera.objects.filter(
                    cuadrilla__jefe=jefe
                )
        self.fields["labor"].queryset = Labor.objects.filter(activa=True)
