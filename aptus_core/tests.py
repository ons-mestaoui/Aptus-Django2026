from django.test import TestCase, Client
from django.urls import reverse

class AptusCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        from accounts.models import Utilisateur
        admin = Utilisateur.objects.create(
            nom="Admin", prenom="Super", email="admin.test@aptus.tn",
            mot_de_passe="admin123", role="Admin"
        )
        session = self.client.session
        session['id_utilisateur'] = admin.id_utilisateur
        session['user_id'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_accounts_crud_list(self):
        response = self.client.get(reverse('accounts:utilisateur_list'))
        self.assertEqual(response.status_code, 200)

    def test_jobs_crud_list(self):
        response = self.client.get(reverse('jobs:offre_list'))
        self.assertEqual(response.status_code, 200)

    def test_cv_studio_crud_list(self):
        response = self.client.get(reverse('cv_studio:cv_list'))
        self.assertEqual(response.status_code, 200)

    def test_training_crud_list(self):
        response = self.client.get(reverse('training:formation_list'))
        self.assertEqual(response.status_code, 200)

    def test_market_crud_list(self):
        response = self.client.get(reverse('market:rapport_list'))
        self.assertEqual(response.status_code, 200)
