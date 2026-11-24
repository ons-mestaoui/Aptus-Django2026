from datetime import date, datetime, timedelta, timezone as dt_timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import Utilisateur, Entreprise
from jobs.models import OffreEmploi
from jobs.forms import OffreEmploiForm
from training.models import Formation
from training.forms import FormationForm


class DatePreservationOnEditTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = Utilisateur.objects.create(
            nom="Admin",
            prenom="Super",
            email="admin.dates@aptus.tn",
            mot_de_passe="admin1234",
            role="Admin",
        )
        self.entreprise_user = Utilisateur.objects.create(
            nom="Directeur",
            prenom="RH",
            email="rh.dates@aptus.tn",
            mot_de_passe="secret1234",
            role="Entreprise",
        )
        self.entreprise = Entreprise.objects.create(
            utilisateur=self.entreprise_user,
            raison_sociale="Aptus Tech",
            secteur="IT",
        )
        self.tuteur_user = Utilisateur.objects.create(
            nom="Formateur",
            prenom="Ali",
            email="tuteur.dates@aptus.tn",
            mot_de_passe="secret1234",
            role="Tuteur",
        )

        self.future_expir = date.today() + timedelta(days=30)
        self.offre = OffreEmploi.objects.create(
            entreprise=self.entreprise,
            titre="Ingénieur Python",
            description="Développement backend Django.",
            competences_requises="Python, Django",
            salaire=3500.0,
            date_expir=self.future_expir,
            domaine="Informatique",
            experience_requise="3 ans",
            question="Quelle est votre expérience avec Django ?",
        )

        # Datetimes in the future in Europe/Paris
        base_future = timezone.localtime(timezone.now() + timedelta(days=10)).replace(
            hour=9, minute=30, second=0, microsecond=0
        )
        self.formation_start = base_future
        self.formation_end = base_future + timedelta(days=2, hours=7, minutes=30)
        self.formation = Formation.objects.create(
            titre="Architecture Django",
            description="<p>Programme avancé</p>",
            domaine="Développement Web",
            niveau="Avancé",
            duree="16h",
            date_formation=self.formation_start,
            date_fin=self.formation_end,
            tuteur=self.tuteur_user,
            is_online=True,
            lien_api_room="https://meet.jit.si/aptus-django",
        )

    def _login_session(self, user):
        session = self.client.session
        session["user_id"] = user.id_utilisateur
        session["id_utilisateur"] = user.id_utilisateur
        session["role"] = user.role
        session["user_email"] = user.email
        session.save()

    # ── OffreEmploi tests ──

    def test_offre_form_renders_iso_date_value(self):
        form = OffreEmploiForm(instance=self.offre)
        rendered = str(form["date_expir"])
        expected_val = self.future_expir.strftime("%Y-%m-%d")
        self.assertIn(f'value="{expected_val}"', rendered)
        self.assertNotIn(self.future_expir.strftime("%d/%m/%Y"), rendered)

    def test_offre_edit_entreprise_frontoffice_renders_and_preserves_date(self):
        self._login_session(self.entreprise_user)
        url = reverse("jobs:offre_update", args=[self.offre.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")
        expected_val = self.future_expir.strftime("%Y-%m-%d")
        self.assertIn(f'name="date_expir" value="{expected_val}"', html)

        res_post = self.client.post(
            url,
            {
                "entreprise": self.entreprise.pk,
                "titre": "Ingénieur Python Senior",
                "description": self.offre.description,
                "competences_requises": self.offre.competences_requises,
                "salaire": "4000",
                "date_expir": expected_val,
                "domaine": self.offre.domaine,
                "experience_requise": self.offre.experience_requise,
                "question": self.offre.question,
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.titre, "Ingénieur Python Senior")
        self.assertEqual(self.offre.date_expir, self.future_expir)

    def test_offre_edit_admin_backoffice_renders_and_preserves_date(self):
        self._login_session(self.admin_user)
        url = reverse("backoffice_offre_update", args=[self.offre.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")
        expected_val = self.future_expir.strftime("%Y-%m-%d")
        self.assertIn(f'name="date_expir" value="{expected_val}"', html)

        res_post = self.client.post(
            url,
            {
                "entreprise": self.entreprise.pk,
                "titre": "Ingénieur Python Backoffice",
                "description": self.offre.description,
                "competences_requises": self.offre.competences_requises,
                "salaire": "4200",
                "date_expir": expected_val,
                "domaine": self.offre.domaine,
                "experience_requise": self.offre.experience_requise,
                "question": self.offre.question,
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.titre, "Ingénieur Python Backoffice")
        self.assertEqual(self.offre.date_expir, self.future_expir)

    def test_offre_edit_past_expiration_date_preserved_and_min_allows_it(self):
        past_pub = date.today() - timedelta(days=15)
        past_expir = date.today() - timedelta(days=5)
        OffreEmploi.objects.filter(pk=self.offre.pk).update(
            date_publication=past_pub, date_expir=past_expir
        )
        self.offre.refresh_from_db()

        self._login_session(self.entreprise_user)
        url = reverse("jobs:offre_update", args=[self.offre.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")
        self.assertIn(f'value="{past_expir.strftime("%Y-%m-%d")}"', html)
        self.assertIn(f'min="{past_pub.strftime("%Y-%m-%d")}"', html)

        res_post = self.client.post(
            url,
            {
                "entreprise": self.entreprise.pk,
                "titre": "Offre Expirée Mise à Jour",
                "description": self.offre.description,
                "competences_requises": self.offre.competences_requises,
                "salaire": "3500",
                "date_expir": past_expir.strftime("%Y-%m-%d"),
                "domaine": self.offre.domaine,
                "experience_requise": self.offre.experience_requise,
                "question": self.offre.question,
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.titre, "Offre Expirée Mise à Jour")
        self.assertEqual(self.offre.date_expir, past_expir)

    # ── Formation tests ──

    def test_formation_form_renders_iso_datetime_local_values_in_local_tz(self):
        utc_start = datetime(2027, 3, 15, 8, 45, tzinfo=dt_timezone.utc)
        utc_end = datetime(2027, 3, 17, 16, 15, tzinfo=dt_timezone.utc)
        f = Formation.objects.create(
            titre="Formation TZ",
            description="Test TZ",
            domaine="Cloud",
            niveau="Intermédiaire",
            date_formation=utc_start,
            date_fin=utc_end,
            tuteur=self.tuteur_user,
        )
        form = FormationForm(instance=f)
        start_html = str(form["date_formation"])
        end_html = str(form["date_fin"])

        expected_start = timezone.localtime(utc_start).strftime("%Y-%m-%dT%H:%M")
        expected_end = timezone.localtime(utc_end).strftime("%Y-%m-%dT%H:%M")
        self.assertIn(f'value="{expected_start}"', start_html)
        self.assertIn(f'value="{expected_end}"', end_html)

    def test_formation_edit_admin_backoffice_renders_and_preserves_dates(self):
        self._login_session(self.admin_user)
        url = reverse("backoffice_formation_update", args=[self.formation.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")

        expected_start = timezone.localtime(self.formation_start).strftime("%Y-%m-%dT%H:%M")
        expected_end = timezone.localtime(self.formation_end).strftime("%Y-%m-%dT%H:%M")
        self.assertIn(f'name="date_formation" value="{expected_start}"', html)
        self.assertIn(f'name="date_fin" value="{expected_end}"', html)

        res_post = self.client.post(
            url,
            {
                "titre": "Architecture Django & Celery",
                "description": "<p>Programme mis à jour</p>",
                "domaine": self.formation.domaine,
                "niveau": self.formation.niveau,
                "duree": "20h",
                "date_formation": expected_start,
                "date_fin": expected_end,
                "tuteur": self.tuteur_user.pk,
                "is_online": "True",
                "lien_api_room": self.formation.lien_api_room,
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.titre, "Architecture Django & Celery")
        self.assertEqual(
            timezone.localtime(self.formation.date_formation),
            timezone.localtime(self.formation_start),
        )
        self.assertEqual(
            timezone.localtime(self.formation.date_fin),
            timezone.localtime(self.formation_end),
        )

    def test_formation_edit_frontoffice_route_renders_and_preserves_dates(self):
        self._login_session(self.admin_user)
        url = reverse("training:formation_update", args=[self.formation.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")

        expected_start = timezone.localtime(self.formation_start).strftime("%Y-%m-%dT%H:%M")
        expected_end = timezone.localtime(self.formation_end).strftime("%Y-%m-%dT%H:%M")
        self.assertIn(f'value="{expected_start}"', html)
        self.assertIn(f'value="{expected_end}"', html)

        res_post = self.client.post(
            url,
            {
                "titre": "Architecture Django Front Route",
                "description": "<p>Programme mis à jour</p>",
                "domaine": self.formation.domaine,
                "niveau": self.formation.niveau,
                "duree": "18h",
                "date_formation": expected_start,
                "date_fin": expected_end,
                "tuteur": self.tuteur_user.pk,
                "is_online": "True",
                "lien_api_room": self.formation.lien_api_room,
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.titre, "Architecture Django Front Route")
        self.assertEqual(
            timezone.localtime(self.formation.date_formation),
            timezone.localtime(self.formation_start),
        )
        self.assertEqual(
            timezone.localtime(self.formation.date_fin),
            timezone.localtime(self.formation_end),
        )

    def test_formation_edit_past_dates_unchanged_succeeds_and_preserves_dates(self):
        past_start = timezone.localtime(timezone.now() - timedelta(days=3)).replace(
            hour=10, minute=15, second=42, microsecond=0
        )
        past_end = past_start + timedelta(days=1, hours=4)
        Formation.objects.filter(pk=self.formation.pk).update(
            date_formation=past_start, date_fin=past_end
        )
        self.formation.refresh_from_db()

        self._login_session(self.admin_user)
        url = reverse("backoffice_formation_update", args=[self.formation.pk])

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 200)
        html = res_get.content.decode("utf-8")

        rendered_start = past_start.strftime("%Y-%m-%dT%H:%M")
        rendered_end = past_end.strftime("%Y-%m-%dT%H:%M")
        self.assertIn(f'value="{rendered_start}"', html)
        self.assertIn(f'value="{rendered_end}"', html)
        self.assertIn(f'min="{rendered_start}"', html)

        res_post = self.client.post(
            url,
            {
                "titre": "Formation Passée Corrigée",
                "description": "<p>Typo corrigée</p>",
                "domaine": self.formation.domaine,
                "niveau": self.formation.niveau,
                "duree": self.formation.duree,
                "date_formation": rendered_start,
                "date_fin": rendered_end,
                "tuteur": self.tuteur_user.pk,
                "is_online": "False",
            },
        )
        self.assertEqual(res_post.status_code, 302)
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.titre, "Formation Passée Corrigée")
        self.assertEqual(self.formation.date_formation, past_start)
        self.assertEqual(self.formation.date_fin, past_end)

    def test_formation_rejects_changing_date_to_past_and_invalid_end(self):
        past_new = timezone.localtime(timezone.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        form = FormationForm(
            data={
                "titre": "Architecture Django",
                "description": "<p>Test</p>",
                "domaine": "Web",
                "niveau": "Avancé",
                "duree": "10h",
                "date_formation": past_new,
                "date_fin": timezone.localtime(self.formation_end).strftime("%Y-%m-%dT%H:%M"),
                "tuteur": self.tuteur_user.pk,
                "is_online": "False",
            },
            instance=self.formation,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_formation", form.errors)

        valid_start = timezone.localtime(timezone.now() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")
        earlier_end = timezone.localtime(timezone.now() + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M")
        form_end = FormationForm(
            data={
                "titre": "Architecture Django",
                "description": "<p>Test</p>",
                "domaine": "Web",
                "niveau": "Avancé",
                "duree": "10h",
                "date_formation": valid_start,
                "date_fin": earlier_end,
                "tuteur": self.tuteur_user.pk,
                "is_online": "False",
            },
            instance=self.formation,
        )
        self.assertFalse(form_end.is_valid())
        self.assertIn("date_fin", form_end.errors)
