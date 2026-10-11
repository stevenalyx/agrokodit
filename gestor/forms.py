from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Cuartel, LecturaSensor, Predio


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
    pass


class PredioForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Predio
        fields = ["nombre", "ubicacion", "superficie_hectareas"]
        labels = {
            "nombre": "Nombre del predio",
            "ubicacion": "Ubicación",
            "superficie_hectareas": "Superficie (hectáreas)",
        }


class CuartelForm(BootstrapAccesibleMixin, forms.ModelForm):
    class Meta:
        model = Cuartel
        fields = "__all__"


class LecturaSensorForm(BootstrapAccesibleMixin, forms.ModelForm):
    humedad_suelo = forms.FloatField(
        label="Humedad del suelo (%)", min_value=0, max_value=100,
        help_text="Valor entre 0 y 100.",
    )
    temperatura = forms.FloatField(
        label="Temperatura (°C)", min_value=-30, max_value=70,
    )
    ph = forms.FloatField(
        label="pH del suelo", min_value=0, max_value=14,
        help_text="Escala de 0 a 14.",
    )
    bateria = forms.IntegerField(
        label="Nivel de batería del sensor (%)", min_value=0, max_value=100,
    )

    class Meta:
        model = LecturaSensor
        fields = ["cuartel"]

    def save(self, commit=True):
        self.instance.telemetria_dinamica = {
            "humedad_suelo": self.cleaned_data["humedad_suelo"],
            "temperatura": self.cleaned_data["temperatura"],
            "ph": self.cleaned_data["ph"],
            "bateria": self.cleaned_data["bateria"],
        }
        return super().save(commit=commit)