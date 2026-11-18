from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

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


class AgroKODITDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="test-pass-123"
        )
        self.worker_group = Group.objects.create(name="Trabajador")
        self.boss_group = Group.objects.create(name="Jefe de cuadrilla")
        view_permission = Permission.objects.get(
            content_type__app_label="gestor",
            codename="view_registrojornada",
        )
        change_permission = Permission.objects.get(
            content_type__app_label="gestor",
            codename="change_registrojornada",
        )
        self.worker_group.permissions.add(view_permission)
        self.boss_group.permissions.add(view_permission)
        self.boss_group.permissions.add(change_permission)

        self.boss = User.objects.create_user(username="jefe", password="test-pass-123")
        self.boss.groups.add(self.boss_group)
        self.boss_profile = JCuadrilla.objects.create(
            user=self.boss, grupo=self.boss_group
        )
        other_boss = User.objects.create_user(
            username="otro-jefe", password="test-pass-123"
        )
        other_boss_group = Group.objects.create(name="Otro jefe")
        other_boss_profile = JCuadrilla.objects.create(
            user=other_boss, grupo=other_boss_group
        )

        self.worker = User.objects.create_user(
            username="trabajador", password="test-pass-123"
        )
        self.worker.groups.add(self.worker_group)
        worker_profile = Trabajador.objects.create(
            user=self.worker, grupo=self.worker_group
        )
        partner = User.objects.create_user(
            username="compañero", password="test-pass-123"
        )
        partner_profile = Trabajador.objects.create(
            user=partner, grupo=self.worker_group
        )
        other_worker = User.objects.create_user(
            username="otro-trabajador", password="test-pass-123"
        )
        other_worker_profile = Trabajador.objects.create(
            user=other_worker, grupo=self.worker_group
        )
        other_partner = User.objects.create_user(
            username="otro-compañero", password="test-pass-123"
        )
        other_partner_profile = Trabajador.objects.create(
            user=other_partner, grupo=self.worker_group
        )

        self.team = Cuadrilla.objects.create(
            nombre="Cuadrilla norte", jefe=self.boss_profile
        )
        other_team = Cuadrilla.objects.create(
            nombre="Cuadrilla sur", jefe=other_boss_profile
        )
        self.collera = Collera.objects.create(
            cuadrilla=self.team,
            trabajador_1=worker_profile,
            trabajador_2=partner_profile,
        )
        other_collera = Collera.objects.create(
            cuadrilla=other_team,
            trabajador_1=other_worker_profile,
            trabajador_2=other_partner_profile,
        )

        predio = Predio.objects.create(
            nombre="Predio de prueba",
            ubicacion="Valle",
            superficie_hectareas="10.00",
        )
        huerto = Huerto.objects.create(predio=predio, nombre="Huerto uno")
        self.cuartel = Cuartel.objects.create(
            huerto=huerto,
            nombre="Cuartel uno",
            superficie_hectareas="2.50",
        )
        labor = Labor.objects.create(nombre="Cosecha")
        self.jornada = RegistroJornada.objects.create(
            collera=self.collera,
            cuartel=self.cuartel,
            labor=labor,
            kilos_producidos="120.00",
            calidad=RegistroJornada.Calidad.EXPORTACION,
        )
        self.other_jornada = RegistroJornada.objects.create(
            collera=other_collera,
            cuartel=self.cuartel,
            labor=labor,
            kilos_producidos="80.00",
            calidad=RegistroJornada.Calidad.NACIONAL,
        )

    def test_collera_database_constraint_requires_two_distinct_workers(self):
        worker_profile = Trabajador.objects.get(user=self.worker)
        with self.assertRaises(ValidationError):
            Collera(
                cuadrilla=self.team,
                trabajador_1=worker_profile,
                trabajador_2=worker_profile,
            ).full_clean()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Collera.objects.create(
                    cuadrilla=self.team,
                    trabajador_1=worker_profile,
                    trabajador_2=worker_profile,
                )

    def test_worker_dashboard_only_shows_own_collera(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jornadas"], 1)
        self.assertEqual(response.context["total_kilos"], 120)

    def test_jefe_dashboard_only_shows_assigned_teams(self):
        self.client.force_login(self.boss)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jornadas"], 1)
        self.assertEqual(response.context["jornadas_pendientes"], 1)

    def test_admin_dashboard_reports_global_production(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jornadas"], 2)
        self.assertEqual(response.context["total_kilos"], 200)
        self.assertEqual(response.context["total_predios"], 1)

    def test_predio_detail_renders_nested_huertos_and_cuarteles(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("predio_detail", args=[self.cuartel.huerto.predio_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Huerto uno")
        self.assertContains(response, "Cuartel uno")
        self.assertContains(response, "2,50 ha")

    def test_jornada_creation_form_renders(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("jornada_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kilos producidos")
        self.assertContains(response, "Exportación")

    def test_collera_can_be_created_from_the_site(self):
        self.client.force_login(self.admin)
        worker_one = Trabajador.objects.get(user__username="trabajador")
        worker_two = Trabajador.objects.get(user__username="compañero")
        response = self.client.post(
            reverse("collera_create"),
            {
                "cuadrilla": self.team.pk,
                "trabajador_1": worker_one.pk,
                "trabajador_2": worker_two.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Collera.objects.filter(cuadrilla=self.team).count(), 2)

    def test_management_pages_render_for_administrator_role(self):
        admin_group = Group.objects.create(name="Administrador")
        role_admin = User.objects.create_user(username="admin-rol")
        role_admin.groups.add(admin_group)
        self.client.force_login(role_admin)

        for page_name in (
            "cuadrilla_list",
            "collera_list",
            "labor_list",
            "personal_list",
            "personal_create",
        ):
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                self.assertEqual(response.status_code, 200)

        self.assertContains(self.client.get(reverse("collera_list")), "Nueva collera")

    def test_personal_can_be_created_with_its_agricultural_profile(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("personal_create"),
            {
                "username": "nuevo-trabajador",
                "first_name": "Nuevo",
                "last_name": "Trabajador",
                "email": "nuevo@example.com",
                "rol": "Trabajador",
                "password1": "StrongPass!2026",
                "password2": "StrongPass!2026",
            },
        )

        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="nuevo-trabajador")
        self.assertTrue(Trabajador.objects.filter(user=new_user).exists())
        self.assertTrue(new_user.groups.filter(name="Trabajador").exists())

    def test_jefe_can_only_validate_journeys_from_assigned_teams(self):
        self.client.force_login(self.boss)
        list_response = self.client.get(reverse("jornada_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Validar")

        own_response = self.client.post(
            reverse("jornada_validar", args=[self.jornada.pk])
        )
        self.assertEqual(own_response.status_code, 302)
        self.jornada.refresh_from_db()
        self.assertTrue(self.jornada.validado)
        self.assertEqual(self.jornada.validado_por, self.boss_profile)

        other_response = self.client.post(
            reverse("jornada_validar", args=[self.other_jornada.pk])
        )
        self.assertEqual(other_response.status_code, 404)

    def test_predio_with_jornadas_cannot_be_deleted_silently(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("predio_delete", args=[self.cuartel.huerto.predio_id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Predio.objects.filter(pk=self.cuartel.huerto.predio_id).exists())
        self.assertContains(
            self.client.get(reverse("dashboard")),
            "jornadas agrícolas asociadas",
        )
