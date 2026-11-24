import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright
from accounts.models import Utilisateur, Candidat, Entreprise, Administrateur
from jobs.models import OffreEmploi, Candidature
from cv_studio.models import Template, CV
from training.models import Formation
from market.models import RapportMarche
from datetime import date

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"

class AptusPlaywrightUITest(StaticLiveServerTestCase):
    host = 'localhost'

    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
        except Exception:
            pass
        try:
            cls.playwright.stop()
        except Exception:
            pass
        super().tearDownClass()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()
        self._seed_test_data()

    def tearDown(self):
        try:
            self.context.close()
        except Exception:
            pass

    def _seed_test_data(self):
        # Ensure sample data is present in test database
        if not Utilisateur.objects.filter(email='demo@aptus.com').exists():
            u_admin = Utilisateur.objects.create(
                email='demo@aptus.com', prenom='Admin', nom='Aptus', role='Admin'
            )
            admin_obj = Administrateur.objects.create(utilisateur=u_admin, niveau='SuperAdmin')

            u_ent = Utilisateur.objects.create(
                email='ent@aptus.com', prenom='TechCorp', nom='HR', role='Entreprise'
            )
            ent = Entreprise.objects.create(
                utilisateur=u_ent, raison_sociale='TechCorp France', secteur='Technologies'
            )

            u_cand = Utilisateur.objects.create(
                email='cand@aptus.com', prenom='Jean', nom='Dupont', role='Candidat'
            )
            cand = Candidat.objects.create(utilisateur=u_cand, competences='Python, Django, Playwright')

            tpl = Template.objects.create(nom='Modern ATS Clean', est_premium=False)
            CV.objects.create(
                nom_document='CV Jean Dupont', candidat=cand, template=tpl,
                nom_complet='Jean Dupont', titre_poste='Ingénieur Fullstack Django'
            )

            OffreEmploi.objects.create(
                titre='Développeur Fullstack Django / React',
                entreprise=ent,
                domaine='Développement Web',
                salaire=52000.0,
                date_expir=date(2027, 12, 31),
                description='Poste pour ingénieur autonome et rigoureux.'
            )

            Formation.objects.create(
                titre='Formation Playwright & Django E2E',
                domaine='Qualité Logicielle',
                niveau='Avancé',
                description='Automatisez vos tests E2E avec Playwright et Django.',
                is_online=True
            )

            RapportMarche.objects.create(
                titre='Baromètre Marché Emploi Tech 2026',
                admin=admin_obj,
                secteur_principal='Technologies & Digital',
                tendance_generale='Forte demande sur le développement web et IA'
            )

    def test_01_home_page(self):
        """Test navigation to / (Front Landing) and capture screenshot."""
        url = f"{self.live_server_url}/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)
        self.assertIn("Aptus", self.page.title())

        # Screenshot Front Landing
        screenshot_path = SCREENSHOTS_DIR / "front_landing.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_02_dashboard_backoffice(self):
        """Test navigation to /dashboard/ (Admin Backoffice) and capture screenshot."""
        url = f"{self.live_server_url}/dashboard/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)
        self.assertIn("Aptus", self.page.title())

        # Screenshot Backoffice Dashboard
        screenshot_path = SCREENSHOTS_DIR / "admin_dashboard.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_03_utilisateurs_page(self):
        """Test navigation to /utilisateurs/ and capture screenshot."""
        url = f"{self.live_server_url}/utilisateurs/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot utilisateurs
        screenshot_path = SCREENSHOTS_DIR / "utilisateurs.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_04_offres_page(self):
        """Test navigation to /offres/ and capture screenshot."""
        url = f"{self.live_server_url}/offres/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot offres
        screenshot_path = SCREENSHOTS_DIR / "offres.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_05_form_offres_creer(self):
        """Test navigation to /offres/creer/ (Wide Centered Form) and capture screenshot."""
        url = f"{self.live_server_url}/offres/creer/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot form offres creer
        screenshot_path = SCREENSHOTS_DIR / "form_offres_creer.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_06_cv_studio_page(self):
        """Test navigation to /cv-studio/ and capture screenshot."""
        url = f"{self.live_server_url}/cv-studio/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot cv-studio
        screenshot_path = SCREENSHOTS_DIR / "cv_studio.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_07_formations_page(self):
        """Test navigation to /formations/ and capture screenshot."""
        url = f"{self.live_server_url}/formations/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot formations
        screenshot_path = SCREENSHOTS_DIR / "formations.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())

    def test_08_marche_page(self):
        """Test navigation to /marche/ and capture screenshot."""
        url = f"{self.live_server_url}/marche/"
        response = self.page.goto(url, wait_until='networkidle')
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

        # Screenshot marche
        screenshot_path = SCREENSHOTS_DIR / "marche.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        self.assertTrue(screenshot_path.exists())
