import re
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Candidat, Entreprise, Utilisateur
from jobs.models import Candidature, OffreEmploi


class EntrepriseCandidaturesDecisionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.entreprise_user = Utilisateur.objects.create(
            nom="Directeur",
            prenom="RH",
            email="rh.decision@techcorp.com",
            mot_de_passe="secret123",
            role="Entreprise",
            telephone="+216 71 000 111",
        )
        self.entreprise = Entreprise.objects.create(
            utilisateur=self.entreprise_user,
            raison_sociale="TechCorp Solutions",
            secteur="Informatique",
        )
        self.other_entreprise_user = Utilisateur.objects.create(
            nom="Autre",
            prenom="RH",
            email="autre.rh@techcorp.com",
            mot_de_passe="secret123",
            role="Entreprise",
        )
        self.other_entreprise = Entreprise.objects.create(
            utilisateur=self.other_entreprise_user,
            raison_sociale="OtherCorp",
            secteur="Finance",
        )
        self.candidat_user = Utilisateur.objects.create(
            nom="Ben Salah",
            prenom="Sami",
            email="sami.decision@aptus.tn",
            mot_de_passe="secret123",
            role="Candidat",
            telephone="+216 20 111 222",
        )
        self.candidat = Candidat.objects.create(
            utilisateur=self.candidat_user,
            competences="Python, Django",
            niveau_etudes="Bac+5",
        )
        self.offre = OffreEmploi.objects.create(
            titre="Développeur Django",
            description="Développement backend Django",
            salaire=2500.0,
            domaine="Informatique",
            entreprise=self.entreprise,
        )
        self.candidature = Candidature.objects.create(
            candidat=self.candidat,
            offre=self.offre,
            reponses_ques="Très motivé pour rejoindre votre équipe Django.",
            note=88,
            statut="en_attente",
        )
        self.url = reverse("jobs:entreprise_candidatures")
        self._login_as(self.entreprise_user)

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.id_utilisateur
        session["id_utilisateur"] = user.id_utilisateur
        session["role"] = user.role
        session["user_email"] = user.email
        session.save()

    def _get_actions_container_classes(self, html, cand_id):
        pattern = rf'id="decision-actions-{cand_id}"[^>]*class="([^"]+)"'
        match = re.search(pattern, html)
        self.assertIsNotNone(match, f"Container decision-actions-{cand_id} introuvable dans le HTML.")
        return match.group(1).split()

    def test_post_update_statut_accepte_and_refuse_variants(self):
        for submitted_value, expected_statut in [
            ("Accepté", "accepte"),
            ("accepte", "accepte"),
            ("Refusé", "refuse"),
            ("refuse", "refuse"),
            ("Shortlisté", "shortliste"),
            ("shortliste", "shortliste"),
        ]:
            with self.subTest(submitted_value=submitted_value):
                response = self.client.post(
                    self.url,
                    {
                        "id_candidature": self.candidature.id_candidature,
                        "update_statut": submitted_value,
                    },
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, self.url)
                self.candidature.refresh_from_db()
                self.assertEqual(self.candidature.statut, expected_statut)

    def test_post_update_statut_invalid_value_keeps_current_statut(self):
        self.candidature.statut = "accepte"
        self.candidature.save()

        response = self.client.post(
            self.url,
            {
                "id_candidature": self.candidature.id_candidature,
                "update_statut": "Inconnu",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.candidature.refresh_from_db()
        self.assertEqual(self.candidature.statut, "accepte")

    def test_post_update_statut_forbidden_for_other_entreprise(self):
        self._login_as(self.other_entreprise_user)
        response = self.client.post(
            self.url,
            {
                "id_candidature": self.candidature.id_candidature,
                "update_statut": "Accepté",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.candidature.refresh_from_db()
        self.assertEqual(self.candidature.statut, "en_attente")

    def test_en_attente_shows_decision_buttons_without_toggle(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        classes = self._get_actions_container_classes(html, self.candidature.id_candidature)
        self.assertNotIn("d-none", classes)
        self.assertIn("Accepter", html)
        self.assertIn("Refuser", html)
        self.assertIn("Shortlister", html)
        self.assertNotIn("Changer la décision", html)
        self.assertIn("Consulter le CV joint", html)
        self.assertIn("Supprimer", html)

    def test_decided_statuts_hide_decision_buttons_and_render_toggle(self):
        cases = [
            ("accepte", "Acceptée"),
            ("refuse", "Refusée"),
            ("shortliste", "Shortlistée"),
        ]
        for statut, expected_label in cases:
            with self.subTest(statut=statut):
                self.candidature.statut = statut
                self.candidature.save()

                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode("utf-8")

                classes = self._get_actions_container_classes(html, self.candidature.id_candidature)
                self.assertIn("d-none", classes)
                self.assertIn(expected_label, html)
                self.assertIn("Changer la décision", html)
                self.assertIn("js-toggle-decision", html)
                self.assertIn("js-cancel-decision", html)
                self.assertIn("Annuler", html)
                self.assertIn("Supprimer", html)
                self.assertIn("Consulter le CV joint", html)

    def test_delete_candidature_still_works(self):
        response = self.client.post(
            self.url,
            {
                "id_candidature": self.candidature.id_candidature,
                "delete_candidature": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Candidature.objects.filter(pk=self.candidature.id_candidature).exists()
        )
