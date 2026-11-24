from datetime import date
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Administrateur, Utilisateur
from market.models import RapportMarche, ReferenceRapport


class MarketRapportCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = Utilisateur.objects.create(
            nom="Ben Ali",
            prenom="Nadia",
            email="nadia.admin@aptus.tn",
            mot_de_passe="admin1234",
            role="Admin",
        )
        self.cand_user = Utilisateur.objects.create(
            nom="Trabelsi",
            prenom="Youssef",
            email="youssef@aptus.tn",
            mot_de_passe="cand1234",
            role="Candidat",
        )

    def _login_as(self, user):
        session = self.client.session
        session['user_id'] = user.id_utilisateur
        session['id_utilisateur'] = user.id_utilisateur
        session['role'] = user.role
        session['user_email'] = user.email
        session.save()

    def test_create_get_defaults_and_controls(self):
        self._login_as(self.admin_user)
        url = reverse('market:rapport_create')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')

        today_str = timezone.localdate().strftime('%Y-%m-%d')
        self.assertIn(today_str, html)
        self.assertNotIn('id_admin', html)
        self.assertNotIn('Administrateur Signataire', html)
        self.assertIn('TND', html)
        self.assertIn("Références &amp; Sources d'information", html)
        self.assertIn('Tunis', html)
        self.assertIn('Sfax', html)
        self.assertIn('International', html)
        self.assertIn('En hausse', html)
        self.assertIn('En baisse', html)
        # Sidebar active highlight on /marche/creer/
        self.assertRegex(html, r'class="sidebar-link active"[^>]*id="sidebar-veille"')

    def test_create_post_binds_admin_computes_avg_and_saves_references(self):
        self._login_as(self.admin_user)
        res = self.client.post(reverse('market:rapport_create'), {
            'titre': 'Baromètre Tech Tunisie 2026',
            'secteur_principal': 'Data & IA',
            'region': 'Tunis',
            'auteur': 'Observatoire Aptus',
            'date_publication': '2026-11-24',
            'description': 'Résumé exécutif du marché Data en Tunisie.',
            'contenu_detaille': 'Analyse approfondie des rémunérations et profils demandés.',
            'image_couverture': 'https://example.com/cover.png',
            'salaire_min_global': '2000',
            'salaire_max_global': '4000',
            'salaire_moyen_global': '',
            'tendance_generale': 'En hausse',
            'niveau_demande_global': '4',
            'references-TOTAL_FORMS': '2',
            'references-INITIAL_FORMS': '0',
            'references-MIN_NUM_FORMS': '0',
            'references-MAX_NUM_FORMS': '1000',
            'references-0-titre_source': 'INS Tunisie — Enquête Emploi',
            'references-0-url_source': 'https://www.ins.tn/enquete-emploi',
            'references-0-note_source': 'T3 2026, p. 14',
            'references-1-titre_source': 'Tanitjobs Baromètre IT',
            'references-1-url_source': 'https://www.tanitjobs.com/',
            'references-1-note_source': 'Échantillon 1200 offres',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('backoffice_veille'))

        rapport = RapportMarche.objects.get(titre='Baromètre Tech Tunisie 2026')
        admin_profile = Administrateur.objects.get(utilisateur=self.admin_user)
        self.assertEqual(rapport.admin, admin_profile)
        self.assertEqual(rapport.salaire_moyen_global, 3000.0)
        self.assertEqual(rapport.niveau_demande_global, 4)
        self.assertEqual(rapport.image_couverture, 'https://example.com/cover.png')
        self.assertEqual(rapport.references.count(), 2)

    def test_create_post_rejects_min_greater_than_max(self):
        self._login_as(self.admin_user)
        res = self.client.post(reverse('market:rapport_create'), {
            'titre': 'Rapport Invalide Salaires',
            'salaire_min_global': '5000',
            'salaire_max_global': '2500',
            'references-TOTAL_FORMS': '1',
            'references-INITIAL_FORMS': '0',
            'references-MIN_NUM_FORMS': '0',
            'references-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(res.status_code, 200)
        self.assertFalse(RapportMarche.objects.filter(titre='Rapport Invalide Salaires').exists())

    def test_detail_renders_references_and_tnd_without_donnees_brutes(self):
        rapport = RapportMarche.objects.create(
            titre='Étude Cybersécurité 2026',
            secteur_principal='Cybersécurité',
            region='Sousse',
            auteur='Équipe Aptus',
            date_publication=date(2026, 11, 20),
            description='Synthèse cyber.',
            contenu_detaille='Détails complets sur la cybersécurité en Tunisie.',
            image_couverture='https://example.com/cyber.jpg',
            salaire_min_global=2200,
            salaire_moyen_global=3100,
            salaire_max_global=4200,
            tendance_generale='En hausse',
            niveau_demande_global=3,
        )
        ReferenceRapport.objects.create(
            rapport_marche=rapport,
            titre_source='ANSI Tunisie — Rapport Annuel',
            url_source='https://www.ansi.tn/rapport',
            note_source='Section RH Cyber',
        )

        res = self.client.get(reverse('market:rapport_detail', args=[rapport.pk]))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('https://example.com/cyber.jpg', html)
        self.assertIn('Détails complets sur la cybersécurité en Tunisie.', html)
        self.assertIn('20/11/2026', html)
        self.assertIn('3 — Élevé', html)
        self.assertIn('3100 TND', html)
        self.assertIn('ANSI Tunisie — Rapport Annuel', html)
        self.assertIn('https://www.ansi.tn/rapport', html)
        self.assertNotIn('Données Collectées', html)

    def test_update_preserves_custom_values_and_updates_references(self):
        rapport = RapportMarche.objects.create(
            titre='Rapport Legacy',
            region='National',
            tendance_generale='Forte hausse (+7.4%)',
            niveau_demande_global=92,
            salaire_min_global=1500,
            salaire_max_global=2500,
            salaire_moyen_global=2000,
        )
        ref1 = ReferenceRapport.objects.create(
            rapport_marche=rapport,
            titre_source='Source Initiale',
            url_source='https://example.com/old',
            note_source='Note initiale',
        )

        self._login_as(self.admin_user)
        res_get = self.client.get(reverse('market:rapport_update', args=[rapport.pk]))
        self.assertEqual(res_get.status_code, 200)
        get_html = res_get.content.decode('utf-8')
        self.assertIn('id_references-0-id_reference', get_html)
        self.assertIn('value="National" selected', get_html)
        self.assertIn('value="Forte hausse (+7.4%)" selected', get_html)
        self.assertIn('value="92" selected', get_html)

        res_post = self.client.post(reverse('market:rapport_update', args=[rapport.pk]), {
            'titre': 'Rapport Mis à Jour',
            'region': 'National',
            'tendance_generale': 'Forte hausse (+7.4%)',
            'niveau_demande_global': '92',
            'salaire_min_global': '1800',
            'salaire_max_global': '2600',
            'salaire_moyen_global': '',
            'references-TOTAL_FORMS': '2',
            'references-INITIAL_FORMS': '1',
            'references-MIN_NUM_FORMS': '0',
            'references-MAX_NUM_FORMS': '1000',
            'references-0-id_reference': str(ref1.pk),
            'references-0-rapport_marche': str(rapport.pk),
            'references-0-titre_source': 'Source Initiale',
            'references-0-url_source': 'https://example.com/old',
            'references-0-note_source': 'Note initiale',
            'references-0-DELETE': 'on',
            'references-1-id_reference': '',
            'references-1-rapport_marche': str(rapport.pk),
            'references-1-titre_source': 'Nouvelle Source Officielle',
            'references-1-url_source': 'https://example.com/new',
            'references-1-note_source': '2026',
        })
        self.assertEqual(res_post.status_code, 302)

        rapport.refresh_from_db()
        self.assertEqual(rapport.titre, 'Rapport Mis à Jour')
        self.assertEqual(rapport.salaire_moyen_global, 2200.0)
        self.assertIsNotNone(rapport.admin)
        self.assertFalse(ReferenceRapport.objects.filter(pk=ref1.pk).exists())
        self.assertEqual(rapport.references.count(), 1)
        self.assertEqual(rapport.references.first().titre_source, 'Nouvelle Source Officielle')

    def test_backoffice_veille_real_stats_and_delete(self):
        r1 = RapportMarche.objects.create(
            titre='Rapport Finance',
            secteur_principal='Finance',
            salaire_moyen_global=2500,
        )
        r2 = RapportMarche.objects.create(
            titre='Rapport Biotech',
            secteur_principal='Biotech',
            salaire_moyen_global=3500,
        )
        ReferenceRapport.objects.create(rapport_marche=r1, titre_source='BCT Rapport')
        ReferenceRapport.objects.create(rapport_marche=r1, titre_source='CMF Note')
        ReferenceRapport.objects.create(rapport_marche=r2, titre_source='OMS Data')

        self._login_as(self.admin_user)
        res = self.client.get(reverse('backoffice_veille'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('Références Sources', html)
        self.assertIn('3 000 TND', html)
        self.assertIn('2 sources', html)
        self.assertIn('1 source', html)
        self.assertNotIn('42,500 €', html)
        self.assertNotIn('Points de Données', html)

        # Delete confirm page
        res_del_get = self.client.get(reverse('market:rapport_delete', args=[r1.pk]))
        self.assertEqual(res_del_get.status_code, 200)
        del_html = res_del_get.content.decode('utf-8')
        self.assertIn(reverse('backoffice_veille'), del_html)
        self.assertIn('références associées', del_html)
        self.assertNotIn('séries de données', del_html)

        # Delete POST cascades references
        res_del_post = self.client.post(reverse('market:rapport_delete', args=[r1.pk]))
        self.assertEqual(res_del_post.status_code, 302)
        self.assertFalse(RapportMarche.objects.filter(pk=r1.pk).exists())
        self.assertEqual(ReferenceRapport.objects.count(), 1)

    def test_non_admin_cannot_access_market_admin_endpoints(self):
        rapport = RapportMarche.objects.create(titre='Public Report')
        self._login_as(self.cand_user)
        for url in [
            reverse('backoffice_veille'),
            reverse('market:rapport_create'),
            reverse('market:rapport_update', args=[rapport.pk]),
            reverse('market:rapport_delete', args=[rapport.pk]),
        ]:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302)
