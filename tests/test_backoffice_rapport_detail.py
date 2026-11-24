from datetime import date
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Utilisateur
from market.models import RapportMarche, ReferenceRapport


class BackofficeRapportDetailTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = Utilisateur.objects.create(
            nom="Admin",
            prenom="Sonia",
            email="sonia.admin@aptus.tn",
            mot_de_passe="admin1234",
            role="Admin",
        )
        self.cand_user = Utilisateur.objects.create(
            nom="Ben Salah",
            prenom="Karim",
            email="karim.cand@aptus.tn",
            mot_de_passe="cand1234",
            role="Candidat",
        )
        self.rapport = RapportMarche.objects.create(
            titre="Baromètre IA & Cloud Tunisie 2026",
            secteur_principal="Cloud & IA",
            region="Tunis",
            auteur="Observatoire Aptus",
            date_publication=date(2026, 11, 20),
            description="Synthèse exécutive sur les talents Cloud et IA.",
            contenu_detaille=(
                "<p>Forte progression des profils MLOps.</p>"
                "<script>alert('xss')</script>"
                "<p onclick=\"evil()\">Demande soutenue sur le Grand Tunis.</p>"
            ),
            image_couverture="https://example.com/ia-cloud.jpg",
            salaire_min_global=2400,
            salaire_moyen_global=3600,
            salaire_max_global=5200,
            tendance_generale="En hausse",
            niveau_demande_global=4,
        )
        self.reference = ReferenceRapport.objects.create(
            rapport_marche=self.rapport,
            titre_source="INS Tunisie — Indicateurs Emploi Tech",
            url_source="https://www.ins.tn/indicateurs-tech",
            note_source="Édition Q4 2026",
        )

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.id_utilisateur
        session["id_utilisateur"] = user.id_utilisateur
        session["role"] = user.role
        session["user_email"] = user.email
        session.save()

    def test_rapport_admin_eye_link_points_to_backoffice_detail(self):
        self._login_as(self.admin_user)
        res = self.client.get(reverse("backoffice_veille"))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        expected_url = reverse("backoffice_rapport_detail", args=[self.rapport.pk])
        front_detail_url = reverse("market:rapport_detail", args=[self.rapport.pk])
        self.assertEqual(expected_url, f"/backoffice/veille/{self.rapport.pk}/")
        self.assertIn(f'href="{expected_url}"', html)
        self.assertNotIn(f'href="{front_detail_url}"', html)

    def test_backoffice_detail_renders_backoffice_layout_tnd_and_references(self):
        self._login_as(self.admin_user)
        url = reverse("backoffice_rapport_detail", args=[self.rapport.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Backoffice shell intact, no frontoffice navbar
        self.assertIn('id="sidebar"', html)
        self.assertRegex(html, r'class="sidebar-link active"[^>]*id="sidebar-veille"')
        self.assertNotIn('id="landing-nav"', html)
        self.assertNotIn('class="landing-nav"', html)

        # Report fields & sanitized rich HTML
        self.assertIn("https://example.com/ia-cloud.jpg", html)
        self.assertIn("Cloud &amp; IA", html)
        self.assertIn("20/11/2026", html)
        self.assertIn("Tunis", html)
        self.assertIn("Observatoire Aptus", html)
        self.assertIn("Synthèse exécutive sur les talents Cloud et IA.", html)
        self.assertIn("Forte progression des profils MLOps.", html)
        self.assertIn("Demande soutenue sur le Grand Tunis.", html)
        self.assertNotIn("<script>alert('xss')</script>", html)
        self.assertNotIn('onclick="evil()"', html)
        self.assertNotIn("evil()", html)

        # Statistiques Salariales (TND) & References
        self.assertIn("Statistiques Salariales (TND)", html)
        self.assertIn("2400 TND", html)
        self.assertIn("3600 TND", html)
        self.assertIn("5200 TND", html)
        self.assertIn("En hausse", html)
        self.assertIn("4 — Très élevé / Critique", html)
        self.assertIn("Références &amp; Sources", html)
        self.assertIn("INS Tunisie — Indicateurs Emploi Tech", html)
        self.assertIn('href="https://www.ins.tn/indicateurs-tech"', html)

        # Backoffice navigation & actions
        self.assertIn(reverse("backoffice_veille"), html)
        self.assertIn("Retour à la veille marché", html)
        self.assertIn(reverse("market:rapport_update", args=[self.rapport.pk]), html)
        self.assertIn("aptusConfirmDelete", html)
        self.assertIn(reverse("market:rapport_delete", args=[self.rapport.pk]), html)

    def test_non_admin_and_anonymous_redirected_from_backoffice_detail(self):
        url = reverse("backoffice_rapport_detail", args=[self.rapport.pk])

        # Anonymous
        res_anon = self.client.get(url)
        self.assertEqual(res_anon.status_code, 302)

        # Candidat (non-admin)
        self._login_as(self.cand_user)
        res_cand = self.client.get(url)
        self.assertEqual(res_cand.status_code, 302)

    def test_frontoffice_rapport_detail_remains_intact(self):
        res = self.client.get(reverse("market:rapport_detail", args=[self.rapport.pk]))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")
        self.assertIn('id="landing-nav"', html)
