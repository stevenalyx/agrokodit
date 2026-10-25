from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from gestor.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "cuentas/login/",
        auth_views.LoginView.as_view(authentication_form=LoginForm),
        name="login",
    ),
    path("cuentas/", include("django.contrib.auth.urls")),
    # /dashboard/ redirige al inicio, donde vive el dashboard (name="dashboard")
    path("dashboard/", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("", include("gestor.urls")),
]
