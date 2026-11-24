from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Utilisateur, Candidat, Entreprise, Profil
from cv_studio.models import CV, Template, RapportIA
from cv_studio.forms import CVForm


class CVStudioCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = Utilisateur.objects.create(
            nom="Ben Ali",
            prenom="Amira",
            email="amira@aptus.tn",
            mot_de_passe="secret123",
            role="Candidat",
            telephone="+216 22 111 222",
        )
        self.candidat_a = Candidat.objects.create(
            utilisateur=self.user_a,
            competences="Python, Django",
            niveau_etudes="Ingénieur",
        )
        Profil.objects.create(
            utilisateur=self.user_a,
            ville="Tunis",
            pays="Tunisie",
        )

        self.user_b = Utilisateur.objects.create(
            nom="Trabelsi",
            prenom="Karim",
            email="karim@aptus.tn",
            mot_de_passe="secret123",
            role="Candidat",
            telephone="+216 55 333 444",
        )
        self.candidat_b = Candidat.objects.create(
            utilisateur=self.user_b,
            competences="Java, Spring",
        )

        self.entreprise_user = Utilisateur.objects.create(
            nom="RH",
            prenom="Corp",
            email="corp@aptus.tn",
            mot_de_passe="secret123",
            role="Entreprise",
        )
        Entreprise.objects.create(utilisateur=self.entreprise_user, raison_sociale="CorpTN")

        self.template = Template.objects.create(
            nom="Moderne ATS",
            description="tech, ats",
            structure_html=(
                '<!DOCTYPE html><html><head><style>'
                'body { background: #333; padding: 20px; }'
                '.cv-name { color: var(--cv-accent, #6b34a3); }'
                '</style></head><body>'
                '<div class="cv-container">'
                '<img id="preview-photo" style="display:none;" src="">'
                '<h1 id="preview-nomComplet" class="cv-name">Nom</h1>'
                '<h2 id="preview-titrePoste" class="cv-title">Titre</h2>'
                '<div id="preview-infoContact">Contact</div>'
                '<div id="preview-resume">Résumé</div>'
                '<div id="preview-experience">Expérience</div>'
                '<div id="preview-formation">Formation</div>'
                '<div id="preview-competences">Compétences</div>'
                '<div id="preview-langues">Langues</div>'
                '</div></body></html>'
            ),
            est_premium=False,
        )

    def _login(self, user):
        session = self.client.session
        session['user_id'] = user.id_utilisateur
        session['id_utilisateur'] = user.id_utilisateur
        session['role'] = user.role
        session.save()

    def test_auth_and_role_guards(self):
        res_list = self.client.get(reverse('cv_studio:cv_list'))
        self.assertEqual(res_list.status_code, 302)
        self.assertIn(reverse('login'), res_list.url)

        res_create = self.client.get(reverse('cv_studio:cv_create'))
        self.assertEqual(res_create.status_code, 302)

        self._login(self.entreprise_user)
        res_non_cand = self.client.get(reverse('cv_studio:cv_create'))
        self.assertEqual(res_non_cand.status_code, 302)
        self.assertEqual(res_non_cand.url, reverse('jobs:offre_list'))

    def test_cv_form_removes_idor_and_statut_fields(self):
        form = CVForm()
        self.assertNotIn('candidat', form.fields)
        self.assertNotIn('statut', form.fields)
        for expected in ('url_photo', 'couleur_theme', 'email', 'telephone', 'localisation'):
            self.assertIn(expected, form.fields)

    def test_cv_create_idor_prevention_and_no_dummy_rapport_ia(self):
        self._login(self.user_a)
        get_res = self.client.get(reverse('cv_studio:cv_create') + f'?template_id={self.template.pk}')
        self.assertEqual(get_res.status_code, 200)
        html = get_res.content.decode('utf-8')
        self.assertIn('CV Studio Aptus', html)
        self.assertNotIn('Aptus Admin', html)
        self.assertNotIn('name="candidat"', html)
        self.assertNotIn('Polish via IA', html)
        self.assertIn('6', html)
        self.assertIn('template-preview-frame', html)

        sample_photo = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
        post_res = self.client.post(reverse('cv_studio:cv_create'), {
            'candidat': self.candidat_b.pk,  # Attempted IDOR tampering
            'statut': 'Pirate',
            'template': self.template.pk,
            'nom_document': '',  # Should auto-default to "CV Amira Ben Ali"
            'nom_complet': 'Amira Ben Ali',
            'titre_poste': 'Ingénieure Logiciel',
            'email': 'amira.pro@aptus.tn',
            'telephone': '+216 22 111 222',
            'localisation': 'Tunis, Tunisie',
            'resume': 'Développeuse Python et Django passionnée par les systèmes fiables.',
            'experience': 'Développeuse Backend — TechTN\n2023 - Présent\n• APIs Django REST',
            'formation': 'Diplôme Ingénieur ★\nINSAT | 2018 - 2023',
            'competences': 'Python, Django, PostgreSQL',
            'langues': 'Français - C2\nAnglais - B2',
            'url_photo': sample_photo,
            'couleur_theme': '#2563EB',
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertEqual(post_res.url, reverse('cv_studio:cv_list'))

        # No dummy RapportIA created
        self.assertEqual(RapportIA.objects.count(), 0)

        cv = CV.objects.get(nom_complet='Amira Ben Ali')
        self.assertEqual(cv.candidat, self.candidat_a)
        self.assertNotEqual(cv.candidat, self.candidat_b)
        self.assertEqual(cv.nom_document, 'CV Amira Ben Ali')
        self.assertEqual(cv.info_contact, 'amira.pro@aptus.tn | +216 22 111 222 | Tunis, Tunisie')
        self.assertEqual(cv.url_photo, sample_photo)
        self.assertEqual(cv.couleur_theme, '#2563eb')
        self.assertEqual(cv.statut, 'Actif')

    def test_cv_form_validation_rules(self):
        form_bad_email = CVForm(data={
            'nom_complet': 'Amira Ben Ali',
            'titre_poste': 'Dev',
            'email': 'not-an-email',
            'telephone': '+216 22 111 222',
        })
        self.assertFalse(form_bad_email.is_valid())
        self.assertIn('email', form_bad_email.errors)

        form_bad_phone = CVForm(data={
            'nom_complet': 'Amira Ben Ali',
            'titre_poste': 'Dev',
            'email': 'amira@aptus.tn',
            'telephone': '1234',
        })
        self.assertFalse(form_bad_phone.is_valid())
        self.assertIn('telephone', form_bad_phone.errors)

    def test_cv_update_parses_contact_and_blocks_cross_user_access(self):
        cv = CV.objects.create(
            candidat=self.candidat_a,
            template=self.template,
            nom_document='CV Amira',
            nom_complet='Amira Ben Ali',
            titre_poste='Développeuse Python',
            info_contact='amira@aptus.tn | +216 22 111 222 | Sfax, Tunisie',
            langues='Français - C1\nAnglais - B2',
            couleur_theme='#059669',
        )

        # Candidate B cannot view, print, update, or delete Candidate A's CV
        self._login(self.user_b)
        for route in ('cv_studio:cv_detail', 'cv_studio:cv_print', 'cv_studio:cv_update', 'cv_studio:cv_delete'):
            res = self.client.get(reverse(route, args=[cv.pk]))
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res.url, reverse('cv_studio:cv_list'))

        # Candidate A loads update form and sees parsed contact fields
        self._login(self.user_a)
        res_get = self.client.get(reverse('cv_studio:cv_update', args=[cv.pk]))
        self.assertEqual(res_get.status_code, 200)
        form = res_get.context['form']
        self.assertEqual(form.initial.get('email'), 'amira@aptus.tn')
        self.assertEqual(form.initial.get('telephone'), '+216 22 111 222')
        self.assertEqual(form.initial.get('localisation'), 'Sfax, Tunisie')
        self.assertEqual(form.initial.get('couleur_theme'), '#059669')

        # Update with tampered candidat still keeps candidat_a
        res_post = self.client.post(reverse('cv_studio:cv_update', args=[cv.pk]), {
            'candidat': self.candidat_b.pk,
            'template': self.template.pk,
            'nom_document': 'CV Amira Senior',
            'nom_complet': 'Amira Ben Ali',
            'titre_poste': 'Lead Python',
            'email': 'amira.lead@aptus.tn',
            'telephone': '+216 22 999 000',
            'localisation': 'Tunis, Tunisie',
            'couleur_theme': '#dc2626',
            'langues': 'Français - C2',
        })
        self.assertEqual(res_post.status_code, 302)
        cv.refresh_from_db()
        self.assertEqual(cv.candidat, self.candidat_a)
        self.assertEqual(cv.nom_document, 'CV Amira Senior')
        self.assertEqual(cv.info_contact, 'amira.lead@aptus.tn | +216 22 999 000 | Tunis, Tunisie')
        self.assertEqual(cv.couleur_theme, '#dc2626')

    def test_cv_list_detail_and_print_rendering(self):
        cv_with_tpl = CV.objects.create(
            candidat=self.candidat_a,
            template=self.template,
            nom_document='CV Moderne',
            nom_complet='Amira Ben Ali',
            titre_poste='Data Engineer',
            info_contact='amira@aptus.tn | +216 22 111 222 | Tunis',
            resume='Experte data pipelines.',
            experience='Data Engineer — DataCo\n2023 - 2026\n• Spark & Airflow',
            formation='Master Data\nFST | 2021 - 2023',
            competences='Python, Spark, SQL',
            langues='Français - C2\nAnglais - C1',
            url_photo='data:image/png;base64,AAAA',
            couleur_theme='#059669',
        )
        cv_no_tpl = CV.objects.create(
            candidat=self.candidat_a,
            template=None,
            nom_document='CV Standard',
            nom_complet='Amira Ben Ali',
            titre_poste='Backend Dev',
            info_contact='custom@aptus.tn | +216 99 888 777 | Sousse',
            langues='Arabe - Natif',
            couleur_theme='#6b34a3',
        )

        self._login(self.user_a)

        # cv_list: compact stats, no oversized AI hero, miniature iframe previews
        res_list = self.client.get(reverse('cv_studio:cv_list'))
        self.assertEqual(res_list.status_code, 200)
        list_html = res_list.content.decode('utf-8')
        self.assertNotIn('RÉVOLUTION IA INTÉGRÉE', list_html)
        self.assertIn('Total des documents', list_html)
        self.assertIn('cv-miniature__iframe', list_html)
        self.assertIn('#059669', list_html)

        # cv_detail: displays photo, contact, languages, theme color, preview, and no broken RapportIA
        res_detail = self.client.get(reverse('cv_studio:cv_detail', args=[cv_with_tpl.pk]))
        self.assertEqual(res_detail.status_code, 200)
        detail_html = res_detail.content.decode('utf-8')
        self.assertIn('data:image/png;base64,AAAA', detail_html)
        self.assertIn('amira@aptus.tn', detail_html)
        self.assertIn('+216 22 111 222', detail_html)
        self.assertIn('Français', detail_html)
        self.assertIn('#059669', detail_html)
        self.assertIn('detail-preview-iframe', detail_html)
        self.assertNotIn('Analyses IA Associées', detail_html)

        # cv_print with template: injects template HTML, --cv-accent, and scopes body CSS
        res_print_tpl = self.client.get(reverse('cv_studio:cv_print', args=[cv_with_tpl.pk]))
        self.assertEqual(res_print_tpl.status_code, 200)
        print_tpl_html = res_print_tpl.content.decode('utf-8')
        self.assertIn('cv-preview-content', print_tpl_html)
        self.assertIn('--cv-accent: #059669', print_tpl_html)
        self.assertIn('preview-nomComplet', print_tpl_html)

        # cv_print without template: renders clean default sheet with NO duplicate email/phone
        res_print_fallback = self.client.get(reverse('cv_studio:cv_print', args=[cv_no_tpl.pk]))
        self.assertEqual(res_print_fallback.status_code, 200)
        fallback_html = res_print_fallback.content.decode('utf-8')
        self.assertIn('cv-sheet', fallback_html)
        self.assertIn('custom@aptus.tn', fallback_html)
        self.assertIn('+216 99 888 777', fallback_html)
        self.assertNotIn('amira@aptus.tn', fallback_html)

    def test_layout_front_navbar_no_wrap(self):
        self._login(self.user_a)
        res = self.client.get(reverse('cv_studio:cv_list'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('flex-wrap: nowrap', html)
