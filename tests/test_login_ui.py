from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from accounts.models import Utilisateur


class LoginUITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "SecretPass123!"
        self.candidat = Utilisateur.objects.create(
            nom="Ben Ali",
            prenom="Amine",
            email="amine.login@aptus.tn",
            mot_de_passe=make_password(self.password),
            role="Candidat",
        )
        self.entreprise = Utilisateur.objects.create(
            nom="RH",
            prenom="TechCorp",
            email="rh.login@aptus.tn",
            mot_de_passe=make_password(self.password),
            role="Entreprise",
        )
        self.admin = Utilisateur.objects.create(
            nom="Admin",
            prenom="Super",
            email="admin.login@aptus.tn",
            mot_de_passe=make_password(self.password),
            role="Admin",
        )
        self.tuteur = Utilisateur.objects.create(
            nom="Prof",
            prenom="Imen",
            email="tuteur.login@aptus.tn",
            mot_de_passe=make_password(self.password),
            role="Tuteur",
        )

    def test_login_get_returns_200_and_split_panel(self):
        res = self.client.get(reverse('login'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('csrfmiddlewaretoken', html)
        self.assertIn('name="email"', html)
        self.assertIn('name="password"', html)
        self.assertIn('id="auth-container"', html)
        self.assertIn('id="signUp"', html)
        self.assertIn('id="signIn"', html)
        self.assertIn(reverse('signup_candidat'), html)
        self.assertIn('/inscription/entreprise/', html)
        self.assertIn('/inscription/tuteur/', html)
        for role in ('candidat', 'entreprise', 'admin', 'tuteur'):
            self.assertIn(f'?demo={role}', html)
        self.assertNotIn('id="sidebar"', html)
        self.assertNotIn('front-navbar', html)

    def test_valid_login_redirects_by_role(self):
        res_cand = self.client.post(reverse('login'), {
            'email': self.candidat.email,
            'password': self.password,
        })
        self.assertEqual(res_cand.status_code, 302)
        self.assertEqual(res_cand.url, reverse('jobs:offre_list'))
        self.assertEqual(self.client.session.get('role'), 'Candidat')

        self.client.logout()
        res_admin = self.client.post(reverse('login'), {
            'email': self.admin.email,
            'password': self.password,
        })
        self.assertEqual(res_admin.status_code, 302)
        self.assertEqual(res_admin.url, reverse('backoffice'))

        self.client.logout()
        res_ent = self.client.post(reverse('login'), {
            'email': self.entreprise.email,
            'password': self.password,
        })
        self.assertEqual(res_ent.status_code, 302)
        self.assertEqual(res_ent.url, reverse('entreprise_posts'))

    def test_invalid_login_displays_inline_error(self):
        res = self.client.post(reverse('login'), {
            'email': self.candidat.email,
            'password': 'wrong-password',
        })
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('Adresse email ou mot de passe incorrect.', html)
        self.assertIsNone(self.client.session.get('user_id'))

    @override_settings(DEBUG=True)
    def test_demo_login_all_roles(self):
        role_targets = {
            'candidat': reverse('jobs:offre_list'),
            'entreprise': reverse('entreprise_posts'),
            'admin': reverse('backoffice'),
            'tuteur': reverse('training:formation_my'),
        }
        for demo_role, expected_url in role_targets.items():
            client = Client()
            res = client.get(f"{reverse('login')}?demo={demo_role}")
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res.url, expected_url)
            self.assertIsNotNone(client.session.get('user_id'))
