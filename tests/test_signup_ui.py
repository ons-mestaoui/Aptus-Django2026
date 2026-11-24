from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Utilisateur, Candidat, Entreprise, Profil
from accounts.auth_helpers import check_user_password


class SignupUITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_signup_candidat_standalone_no_front_navbar(self):
        """GET /inscription/ returns HTTP 200 directly for Candidat without frontoffice navbar."""
        res = self.client.get(reverse('signup_candidat'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('auth-card--wide', html)
        self.assertIn('Créer votre compte', html)
        self.assertIn('step-dot', html)
        self.assertIn('theme-toggle', html)
        self.assertNotIn('front-navbar', html)
        self.assertNotIn('class="navbar', html)
        self.assertNotIn('class="sidebar"', html)

    def test_get_signup_choice_and_roles(self):
        """Role selection, Entreprise, and Tuteur signup pages render HTTP 200 without navbar."""
        for route in ('signup_choice', 'signup_entreprise', 'signup_tuteur'):
            res = self.client.get(reverse(route))
            self.assertEqual(res.status_code, 200, f"Route {route} failed")
            html = res.content.decode('utf-8')
            self.assertNotIn('front-navbar', html)
            self.assertNotIn('class="sidebar"', html)

    def test_post_signup_candidat_creates_user_candidat_profil_and_logs_in(self):
        """POST /inscription/ creates Utilisateur + Candidat + Profil and logs user into session."""
        res = self.client.post(reverse('signup_candidat'), {
            'nom': 'Trabelsi',
            'prenom': 'Yasmine',
            'email': 'Yasmine.Trabelsi@aptus.tn',
            'password': 'Password2026!',
            'password_confirm': 'Password2026!',
            'telephone': '+216 22 111 333',
            'linkedin': 'https://linkedin.com/in/yasmine-trabelsi',
            'date_naissance': '1999-04-12',
            'pays': 'Tunisie',
            'ville': 'Tunis',
            'adresse': '15 Avenue Habib Bourguiba',
            'niveauEtudes': 'Bac+5',
            'niveau': 'Confirmé',
            'competences': 'Python, Django, React',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('jobs:offre_list'))

        user = Utilisateur.objects.get(email='yasmine.trabelsi@aptus.tn')
        self.assertEqual(user.role, 'Candidat')
        self.assertEqual(user.nom, 'Trabelsi')
        self.assertEqual(user.prenom, 'Yasmine')
        self.assertTrue(check_user_password('Password2026!', user.mot_de_passe))

        candidat = Candidat.objects.get(utilisateur=user)
        self.assertEqual(candidat.niveau_etudes, 'Bac+5')
        self.assertEqual(candidat.niveau, 'Confirmé')
        self.assertEqual(candidat.competences, 'Python, Django, React')

        profil = Profil.objects.get(utilisateur=user)
        self.assertEqual(profil.pays, 'Tunisie')
        self.assertEqual(profil.ville, 'Tunis')
        self.assertEqual(profil.adresse, '15 Avenue Habib Bourguiba')
        self.assertEqual(str(profil.date_naissance), '1999-04-12')

        # Session logged in
        self.assertEqual(self.client.session.get('user_id'), user.id_utilisateur)
        self.assertEqual(self.client.session.get('role'), 'Candidat')

    def test_post_signup_candidat_validation_errors_preserve_form_data(self):
        """Mismatched passwords or duplicate email re-renders form with error and preserves inputs."""
        res = self.client.post(reverse('signup_candidat'), {
            'nom': 'Ben Ali',
            'prenom': 'Karim',
            'email': 'karim@aptus.tn',
            'password': 'Password2026!',
            'password_confirm': 'Different2026!',
            'ville': 'Sfax',
        })
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('Les mots de passe ne correspondent pas.', html)
        self.assertIn('Sfax', html)
        self.assertFalse(Utilisateur.objects.filter(email='karim@aptus.tn').exists())

    def test_post_signup_entreprise_creates_records_and_logs_in(self):
        """POST /inscription/entreprise/ creates Utilisateur + Entreprise + Profil and logs in."""
        res = self.client.post(reverse('signup_entreprise'), {
            'raison_sociale': 'Carthage Tech',
            'siret': '12345678901234',
            'secteur': 'Technologie',
            'pays': 'Tunisie',
            'ville': 'Tunis',
            'adresse': 'Lac 2',
            'email': 'rh@carthagetech.tn',
            'telephone': '+216 71 222 333',
            'site_web': 'https://carthagetech.tn',
            'password': 'Password2026!',
            'password_confirm': 'Password2026!',
            'description': 'Startup IA tunisienne.',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('entreprise_posts'))

        user = Utilisateur.objects.get(email='rh@carthagetech.tn')
        self.assertEqual(user.role, 'Entreprise')
        ent = Entreprise.objects.get(utilisateur=user)
        self.assertEqual(ent.raison_sociale, 'Carthage Tech')
        self.assertEqual(ent.siret, '12345678901234')
        profil = Profil.objects.get(utilisateur=user)
        self.assertEqual(profil.site_web, 'https://carthagetech.tn')
        self.assertEqual(self.client.session.get('role'), 'Entreprise')

    def test_post_signup_tuteur_creates_records_and_logs_in(self):
        """POST /inscription/tuteur/ creates Utilisateur(Tuteur) + Profil and logs in."""
        res = self.client.post(reverse('signup_tuteur'), {
            'nom': 'Mansouri',
            'prenom': 'Amira',
            'email': 'amira.tuteur@aptus.tn',
            'password': 'Password2026!',
            'password_confirm': 'Password2026!',
            'specialite': 'Intelligence Artificielle',
            'experience': '7 ans',
            'biographie': 'Formatrice certifiée Python & ML.',
            'pays': 'Tunisie',
            'ville': 'Sousse',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('training:formation_my'))

        user = Utilisateur.objects.get(email='amira.tuteur@aptus.tn')
        self.assertEqual(user.role, 'Tuteur')
        profil = Profil.objects.get(utilisateur=user)
        self.assertIn('Intelligence Artificielle', profil.bio)
        self.assertEqual(self.client.session.get('role'), 'Tuteur')

    def test_landing_page_auth_links_and_stats_labels(self):
        """Landing page preserves clean navbar auth links and readable stats labels."""
        res = self.client.get(reverse('landing'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn(reverse('login'), html)
        self.assertIn(reverse('signup_choice'), html)
        self.assertIn('Explorer les Opportunités', html)
        self.assertIn('.hero-stats-glass .hero__stat-label', html)
