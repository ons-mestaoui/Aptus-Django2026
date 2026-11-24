from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Utilisateur, Candidat, Entreprise, Administrateur
from jobs.models import OffreEmploi, Candidature
from cv_studio.models import Template, CV, RapportIA
from training.models import Formation, Inscription
from market.models import RapportMarche, DonneeMarche

class AptusCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create base test user
        self.user = Utilisateur.objects.create(
            nom="Ben Salah",
            prenom="Sami",
            email="sami@aptus.tn",
            mot_de_passe="secret123",
            role="Candidat",
            telephone="+216 20 111 222"
        )
        self.candidat = Candidat.objects.create(
            utilisateur=self.user,
            competences="Python, Django, SQL",
            niveau_etudes="Bac+5"
        )
        self.entreprise_user = Utilisateur.objects.create(
            nom="Directeur",
            prenom="RH",
            email="rh@techcorp.com",
            mot_de_passe="secret123",
            role="Entreprise",
            telephone="+216 71 000 111"
        )
        self.entreprise = Entreprise.objects.create(
            utilisateur=self.entreprise_user,
            raison_sociale="TechCorp Solutions",
            secteur="Technologies de l'Information"
        )
        self.offre = OffreEmploi.objects.create(
            titre="Développeur Django Fullstack",
            description="Mission de développement web",
            salaire=2500.0,
            domaine="Informatique",
            entreprise=self.entreprise
        )
        self.formation = Formation.objects.create(
            titre="Formation Django & Python Pro",
            description="Maîtriser le framework Django",
            domaine="Informatique",
            niveau="Intermédiaire",
            is_online=True
        )

    def test_landing_status(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_with_login(self):
        admin = Utilisateur.objects.create(
            nom="Admin",
            prenom="Super",
            email="admin@aptus.tn",
            mot_de_passe="admin123",
            role="Admin"
        )
        session = self.client.session
        session['id_utilisateur'] = admin.id_utilisateur
        session['user_id'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session['user_email'] = admin.email
        session.save()
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_accounts_crud(self):
        admin = Utilisateur.objects.create(
            nom="Admin", prenom="Super", email="admin.crud@aptus.tn",
            mot_de_passe="admin1234", role="Admin"
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        # List
        res_list = self.client.get(reverse('accounts:utilisateur_list'))
        self.assertEqual(res_list.status_code, 200)
        # Create
        res_create = self.client.post(reverse('accounts:utilisateur_create'), {
            'nom': 'Nouveau',
            'prenom': 'User',
            'email': 'nouveau@aptus.tn',
            'mot_de_passe': 'pass1234',
            'role': 'Tuteur',
            'telephone': '+216 55 444 333'
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Utilisateur.objects.filter(email='nouveau@aptus.tn').exists())

    def test_jobs_crud(self):
        # List
        res_list = self.client.get(reverse('jobs:offre_list'))
        self.assertEqual(res_list.status_code, 200)
        # Detail
        res_detail = self.client.get(reverse('jobs:offre_detail', args=[self.offre.id_offre]))
        self.assertEqual(res_detail.status_code, 200)

    def test_training_crud(self):
        # List
        res_list = self.client.get(reverse('training:formation_list'))
        self.assertEqual(res_list.status_code, 200)
        # Detail
        res_detail = self.client.get(reverse('training:formation_detail', args=[self.formation.id_formation]))
        self.assertEqual(res_detail.status_code, 200)

    def test_cv_studio_crud(self):
        # Authenticate as candidate
        session = self.client.session
        session['user_id'] = self.user.id_utilisateur
        session['id_utilisateur'] = self.user.id_utilisateur
        session['role'] = 'Candidat'
        session.save()
        # List
        res_list = self.client.get(reverse('cv_studio:cv_list'))
        self.assertEqual(res_list.status_code, 200)

    def test_market_crud(self):
        # List
        res_list = self.client.get(reverse('market:rapport_list'))
        self.assertEqual(res_list.status_code, 200)

    def test_landing_page_navbar_cleanliness(self):
        """Vérifie que la navbar de la landing page n'a que 'Se connecter' et 'S'inscrire', sans Vue Back/Admin."""
        res = self.client.get(reverse('landing'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        nav_html = content.split('<nav class="landing-nav')[1].split('</nav>')[0]
        self.assertIn("Se connecter", nav_html)
        self.assertIn("S'inscrire", nav_html)
        self.assertNotIn("Vue Backoffice", nav_html)
        self.assertNotIn("Vue Admin", nav_html)
        self.assertNotIn("Tableau de bord Admin", nav_html)

    def test_training_enroll_and_viewer_flow(self):
        """Vérifie l'inscription à un cours et l'accès direct au course viewer."""
        session = self.client.session
        session['user_id'] = self.user.id_utilisateur
        session['id_utilisateur'] = self.user.id_utilisateur
        session['role'] = 'Candidat'
        session.save()

        # Inscription
        res_enroll = self.client.post(reverse('training:formation_sinscrire', args=[self.formation.id_formation]))
        self.assertEqual(res_enroll.status_code, 302)
        # Vérification redirection directe vers le viewer
        self.assertIn(reverse('training:formation_viewer', args=[self.formation.id_formation]), res_enroll.url)

        # Accès au viewer
        res_viewer = self.client.get(reverse('training:formation_viewer', args=[self.formation.id_formation]))
        self.assertEqual(res_viewer.status_code, 200)
        self.assertIn("Formation Django", res_viewer.content.decode('utf-8'))

    def test_candidature_delete_and_count_decrement(self):
        """Vérifie la suppression d'une candidature par l'entreprise et la diminution du compteur."""
        cand = Candidature.objects.create(
            candidat=self.candidat,
            offre=self.offre,
            reponses_ques="Motivation forte pour rejoindre TechCorp.",
            statut='en_attente'
        )
        self.assertEqual(Candidature.objects.filter(offre=self.offre).count(), 1)

        session = self.client.session
        session['user_id'] = self.entreprise_user.id_utilisateur
        session['id_utilisateur'] = self.entreprise_user.id_utilisateur
        session['role'] = 'Entreprise'
        session.save()

        # Suppression de la candidature via POST
        res_del = self.client.post(reverse('jobs:entreprise_candidatures'), {
            'delete_candidature': '1',
            'id_candidature': cand.id_candidature
        })
        self.assertEqual(res_del.status_code, 302)
        # Vérifier que le nombre a bien diminué et que la candidature n'existe plus
        self.assertEqual(Candidature.objects.filter(offre=self.offre).count(), 0)

    def test_profile_view_and_update(self):
        """Vérifie l'affichage et la mise à jour de la page profil (/profil/)."""
        session = self.client.session
        session['user_id'] = self.user.id_utilisateur
        session['id_utilisateur'] = self.user.id_utilisateur
        session['role'] = 'Candidat'
        session.save()

        res_get = self.client.get(reverse('profile'))
        self.assertEqual(res_get.status_code, 200)

        # POST update profile
        res_post = self.client.post(reverse('profile'), {
            'nom': 'Ben Salah',
            'prenom': 'Sami Modifie',
            'email': 'sami.modifie@aptus.tn',
            'telephone': '+216 20 999 888',
            'competences': 'Python, Django, React, AI',
            'niveau_etudes': 'Bac+5 Ingénieur'
        })
        self.assertEqual(res_post.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.prenom, 'Sami Modifie')
        self.assertEqual(self.user.email, 'sami.modifie@aptus.tn')

    def test_user_create_full_profile_sync(self):
        """Vérifie la création d'un utilisateur avec tous les champs Image 0 et synchronisation en base."""
        admin = Utilisateur.objects.create(
            nom="Admin", prenom="Super", email="admin.create@aptus.tn",
            mot_de_passe="admin1234", role="Admin"
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res_create = self.client.post(reverse('accounts:utilisateur_create'), {
            'nom': 'Alami',
            'prenom': 'Karim',
            'email': 'karim.alami@aptus.tn',
            'password': 'password1234',
            'password_confirm': 'password1234',
            'role': 'Candidat',
            'telephone': '+216 22 333 444',
            'linkedin': 'https://linkedin.com/in/karimalami',
            'date_naissance': '1998-05-15',
            'pays': 'Tunisie',
            'ville': 'Sousse',
            'adresse': '5 Avenue Habib Bourguiba',
            'niveau_etudes': 'Bac+5',
            'niveau': 'Senior',
            'competences': 'Python, Django, Vue.js'
        })
        self.assertEqual(res_create.status_code, 302)
        
        # Vérification en base SQLite
        u = Utilisateur.objects.filter(email='karim.alami@aptus.tn').first()
        self.assertIsNotNone(u)
        self.assertEqual(u.nom, 'Alami')
        self.assertEqual(u.prenom, 'Karim')
        self.assertEqual(u.role, 'Candidat')
        
        # Profil synchronisé en base
        p = u.profil
        self.assertIsNotNone(p)
        self.assertEqual(p.pays, 'Tunisie')
        self.assertEqual(p.ville, 'Sousse')
        self.assertEqual(p.linkedin, 'https://linkedin.com/in/karimalami')
        
        # Candidat synchronisé en base
        c = u.candidat_profile
        self.assertIsNotNone(c)
        self.assertEqual(c.niveau_etudes, 'Bac+5')
        self.assertIn('Django', c.competences)

    def test_user_delete_direct_and_db_sync(self):
        """Vérifie la suppression directe d'un utilisateur et sa disparition effective de la base SQLite."""
        admin = Utilisateur.objects.create(
            nom="Admin", prenom="Super", email="admin.delete@aptus.tn",
            mot_de_passe="admin1234", role="Admin"
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        u_temp = Utilisateur.objects.create(
            nom="Temporaire",
            prenom="User",
            email="temp.delete@aptus.tn",
            mot_de_passe="pass12345",
            role="Candidat"
        )
        self.assertTrue(Utilisateur.objects.filter(email="temp.delete@aptus.tn").exists())

        # Suppression POST
        res_del = self.client.post(reverse('accounts:utilisateur_delete', args=[u_temp.pk]))
        self.assertEqual(res_del.status_code, 302)
        
        # Vérification en base SQLite
        self.assertFalse(Utilisateur.objects.filter(email="temp.delete@aptus.tn").exists())

    def test_user_database_direct_insert_sync(self):
        """Vérifie qu'un utilisateur inséré directement en base de données s'affiche immédiatement sur le site."""
        admin = Utilisateur.objects.create(
            nom="Admin", prenom="Super", email="admin.test@aptus.tn",
            mot_de_passe="admin1234", role="Admin"
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        # Insertion directe en base SQLite
        u_direct = Utilisateur.objects.create(
            nom="DirectDB",
            prenom="Inserted",
            email="direct.db@aptus.tn",
            mot_de_passe="pass12345",
            role="Entreprise"
        )

        res_list = self.client.get(reverse('backoffice_utilisateurs'))
        self.assertEqual(res_list.status_code, 200)
        content = res_list.content.decode('utf-8')
        self.assertIn("direct.db@aptus.tn", content)
        self.assertIn("DirectDB", content)

    def test_footer_authenticity(self):
        """Vérifie que le footer comporte les 4 colonnes authentiques et non la ligne tronquée."""
        res = self.client.get(reverse('jobs:offre_list'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn("front-footer__grid", content)
        self.assertIn("Plateforme", content)
        self.assertIn("Ressources", content)
        self.assertIn("Légal", content)
        self.assertIn("Fait avec ❤️ en Tunisie", content)

    def test_utilisateur_create_get_rendering(self):
        """Vérifie que GET /utilisateurs/creer/ se rend avec statut 200 sans VariableDoesNotExist."""
        admin = Utilisateur.objects.filter(role='Admin').first()
        if not admin:
            admin = Utilisateur.objects.create(
                nom="Admin", prenom="Super", email="admin.render@aptus.tn",
                mot_de_passe="admin1234", role="Admin"
            )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res = self.client.get(reverse('accounts:utilisateur_create'))
        self.assertEqual(res.status_code, 200)
        self.assertIn("Créer un Utilisateur", res.content.decode('utf-8'))

    def test_formation_delete_confirm_sync(self):
        """Vérifie que la suppression d'une formation avec confirm=1 la supprime directement en BDD."""
        admin = Utilisateur.objects.filter(role='Admin').first()
        if not admin:
            admin = Utilisateur.objects.create(
                nom="Admin", prenom="Super", email="admin.del@aptus.tn",
                mot_de_passe="admin1234", role="Admin"
            )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        f_temp = Formation.objects.create(
            titre="Formation Temp Delete",
            domaine="IT",
            description="Description",
            niveau="Débutant"
        )
        count_before = Formation.objects.count()
        res = self.client.post(reverse('training:formation_delete', args=[f_temp.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Formation.objects.count(), count_before - 1)
        self.assertFalse(Formation.objects.filter(pk=f_temp.pk).exists())

    def test_offre_delete_confirm_sync(self):
        """Vérifie que la suppression d'une offre avec confirm=1 la supprime directement en BDD."""
        admin, _ = Utilisateur.objects.get_or_create(
            email="admin.offre@aptus.test",
            defaults={'nom': 'Admin', 'prenom': 'Super', 'mot_de_passe': 'pass1234', 'role': 'Admin'}
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        o_temp = OffreEmploi.objects.create(
            titre="Offre Temp Delete",
            domaine="Data",
            entreprise=self.entreprise,
            description="Test description"
        )
        count_before = OffreEmploi.objects.count()
        res = self.client.post(reverse('jobs:offre_delete', args=[o_temp.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(OffreEmploi.objects.count(), count_before - 1)
        self.assertFalse(OffreEmploi.objects.filter(pk=o_temp.pk).exists())

    def test_profile_entreprise_fields(self):
        """Vérifie que le profil d'une entreprise affiche bien les informations entreprise et non candidat."""
        session = self.client.session
        session['user_id'] = self.entreprise_user.id_utilisateur
        session['id_utilisateur'] = self.entreprise_user.id_utilisateur
        session['role'] = 'Entreprise'
        session['current_role'] = 'Entreprise'
        session.save()

        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn("Profil Entreprise", content)
        self.assertIn("Informations de l'Entreprise", content)
        self.assertIn("Raison Sociale", content)

    def test_backoffice_topbar_conformance(self):
        """Vérifie que la topbar backoffice ne comporte pas de bouton globe dupliqué."""
        admin, _ = Utilisateur.objects.get_or_create(
            email="admin.topbar@aptus.test",
            defaults={'nom': 'Admin', 'prenom': 'Super', 'mot_de_passe': 'pass1234', 'role': 'Admin'}
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res = self.client.get(reverse('backoffice'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertNotIn("btn-front-switch", content)
        self.assertNotIn("🌐 Voir le site (Vue Front)", content)

    def test_admin_landing_redirects_to_backoffice(self):
        """Vérifie qu'un admin connecté accédant à / est redirigé directement vers le backoffice."""
        admin, _ = Utilisateur.objects.get_or_create(
            email="admin.redir@aptus.test",
            defaults={'nom': 'Admin', 'prenom': 'Aptus', 'mot_de_passe': 'pass1234', 'role': 'Admin'}
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res = self.client.get(reverse('landing'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('backoffice'))

    def test_admin_navbar_has_no_candidate_links(self):
        """Vérifie qu'un admin navigant en front n'a AUCUN lien candidat dans la navbar."""
        admin, _ = Utilisateur.objects.get_or_create(
            email="admin.nav@aptus.test",
            defaults={'nom': 'Admin', 'prenom': 'Aptus', 'mot_de_passe': 'pass1234', 'role': 'Admin'}
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res = self.client.get(reverse('jobs:offre_list'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        # Navbar should NOT have candidate links
        self.assertNotIn("Mes Candidatures", content)
        self.assertNotIn("Générer CV", content)
        self.assertNotIn("Mes CVs", content)
        # Should have the Vue Backoffice switch button
        self.assertIn("Vue Backoffice", content)

    def test_profile_entreprise_no_candidate_fields(self):
        """Vérifie que le profil Entreprise n'affiche AUCUN champ candidat (Niveau d'études, Compétences)."""
        session = self.client.session
        session['user_id'] = self.entreprise_user.id_utilisateur
        session['id_utilisateur'] = self.entreprise_user.id_utilisateur
        session['role'] = 'Entreprise'
        session.save()

        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn("Profil Entreprise", content)
        self.assertIn("Informations de l'Entreprise", content)
        self.assertNotIn("Niveau d'études", content)
        self.assertNotIn("Années d'expérience / Séniorité", content)
        self.assertNotIn("Compétences techniques &amp; outils", content)

    def test_formation_admin_form_standard_page_like_other_forms(self):
        """Vérifie que le formulaire de formation n'est plus flottant et s'ouvre sur une page dédiée comme les autres formulaires backoffice."""
        admin, _ = Utilisateur.objects.get_or_create(
            email="admin.modal@aptus.test",
            defaults={'nom': 'Admin', 'prenom': 'Aptus', 'mot_de_passe': 'pass1234', 'role': 'Admin'}
        )
        session = self.client.session
        session['user_id'] = admin.id_utilisateur
        session['id_utilisateur'] = admin.id_utilisateur
        session['role'] = 'Admin'
        session.save()

        res = self.client.get(reverse('backoffice_formations'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        # Bouton Ajouter une formation redirige vers la page dédiée
        self.assertIn(reverse('backoffice_formation_create'), content)
        # Pas de modal flottant
        self.assertNotIn('id="add-formation-modal"', content)
        self.assertNotIn('onclick="openAddFormationModal()"', content)

        # La page de création dédiée s'ouvre correctement en HTTP 200
        res_create = self.client.get(reverse('backoffice_formation_create'))
        self.assertEqual(res_create.status_code, 200)
        self.assertIn('form', res_create.content.decode('utf-8').lower())
