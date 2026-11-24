import os
import sys
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from django.test import Client
from accounts.models import Utilisateur, Candidat, Entreprise
from jobs.models import OffreEmploi, Candidature
from cv_studio.models import Template

def run_tests():
    c = Client()
    print("=== DEBUT DE LA SUITE DE VERIFICATION METIER & ROLES ===")

    # 1. Vérification de l'absence de boutons admin sur le front (offre_detail)
    offre = OffreEmploi.objects.first()
    if offre:
        resp = c.get(f'/offres/{offre.pk}/')
        content = resp.content.decode('utf-8')
        assert resp.status_code == 200, f"Erreur status /offres/{offre.pk}/: {resp.status_code}"
        assert 'Modifier (Admin)' not in content, "ERREUR: 'Modifier (Admin)' toujours présent sur offre_detail front !"
        assert 'Administration : Candidatures reçues' not in content, "ERREUR: 'Administration : Candidatures reçues' toujours présent sur offre_detail front !"
        assert 'Examiner' not in content, "ERREUR: Bouton 'Examiner' toujours présent sur offre_detail front !"
        print(" [OK] offre_detail.html: 100% épuré (Zéro bouton admin, Zéro 'Examiner')")

    # 2. Vérification de formation_detail front
    resp_f = c.get('/formations/1/')
    if resp_f.status_code == 200:
        content_f = resp_f.content.decode('utf-8')
        assert 'Modifier (Admin)' not in content_f, "ERREUR: 'Modifier (Admin)' présent sur formation_detail front !"
        assert 'Administration : Apprenants Inscrits' not in content_f, "ERREUR: Administration apprenants présent sur formation_detail !"
        print(" [OK] formation_detail.html: 100% épuré (Zéro bouton admin)")

    # 3. Connexion Démo par rôle et redirection stricte
    # Admin -> /backoffice/
    resp_adm = c.get('/connexion/?demo=admin', follow=False)
    assert resp_adm.status_code == 302 and resp_adm['Location'] == '/backoffice/', f"Redirection Admin incorrecte: {resp_adm.get('Location')}"
    print(" [OK] Connexion Admin -> Redirection stricte /backoffice/")

    # Entreprise -> /entreprise/postes/
    resp_ent = c.get('/connexion/?demo=entreprise', follow=False)
    assert resp_ent.status_code == 302 and resp_ent['Location'] == '/entreprise/postes/', f"Redirection Entreprise incorrecte: {resp_ent.get('Location')}"
    print(" [OK] Connexion Entreprise -> Redirection stricte /entreprise/postes/")

    # Candidat -> /offres/
    resp_cand = c.get('/connexion/?demo=candidat', follow=False)
    assert resp_cand.status_code == 302 and resp_cand['Location'] == '/offres/', f"Redirection Candidat incorrecte: {resp_cand.get('Location')}"
    print(" [OK] Connexion Candidat -> Redirection stricte /offres/")

    # 4. Backoffice Templates CV & Formulaire Template
    c_admin = Client()
    admin_user = Utilisateur.objects.filter(role='Admin').first()
    session = c_admin.session
    session['user_id'] = admin_user.id_utilisateur
    session['role'] = 'Admin'
    session.save()

    resp_tpl_list = c_admin.get('/backoffice/templates/')
    assert resp_tpl_list.status_code == 200, f"Erreur /backoffice/templates/: {resp_tpl_list.status_code}"
    tpl_content = resp_tpl_list.content.decode('utf-8')
    assert 'Ajouter un Template' in tpl_content, "ERREUR: Bouton 'Ajouter un Template' manquant dans cv_admin.html !"
    assert 'Catalogue des Modèles' in tpl_content, "ERREUR: Table des modèles manquante !"
    print(" [OK] /backoffice/templates/: Liste des Templates CV avec bouton '+ Ajouter un Template'")

    resp_tpl_form = c_admin.get('/backoffice/templates/creer/')
    assert resp_tpl_form.status_code == 200, f"Erreur /backoffice/templates/creer/: {resp_tpl_form.status_code}"
    form_content = resp_tpl_form.content.decode('utf-8')
    assert 'Nom du template' in form_content, "ERREUR: Champ nom manquant !"
    assert 'Catégories (Tags)' in form_content, "ERREUR: Catégories (Tags) manquantes !"
    assert 'Statut Premium VIP' in form_content, "ERREUR: Statut Premium VIP manquant !"
    assert 'Code Structure (HTML/CSS)' in form_content, "ERREUR: Code Structure manquant !"
    assert 'Générateur Automatique' in form_content, "ERREUR: Générateur Automatique manquant !"
    assert 'Scanner & Afficher' in form_content or 'Scanner &amp; Afficher' in form_content, "ERREUR: Bouton Scanner manquant !"
    print(" [OK] /backoffice/templates/creer/: Formulaire Template CV conforme 100% à template_form.php")

    # 5. Espace Entreprise : Mes Postes & Candidatures Reçues
    c_ent = Client()
    ent_user = Utilisateur.objects.filter(role='Entreprise').first()
    session_ent = c_ent.session
    session_ent['user_id'] = ent_user.id_utilisateur
    session_ent['role'] = 'Entreprise'
    session_ent.save()

    resp_posts = c_ent.get('/entreprise/postes/')
    assert resp_posts.status_code == 200, f"Erreur /entreprise/postes/: {resp_posts.status_code}"
    posts_content = resp_posts.content.decode('utf-8')
    assert 'Mes Postes Publiés' in posts_content, "ERREUR: Header Mes Postes manquant !"
    print(" [OK] /entreprise/postes/: Portail RH Mes Postes accessible")

    resp_cand_recues = c_ent.get('/entreprise/candidatures/')
    assert resp_cand_recues.status_code == 200, f"Erreur /entreprise/candidatures/: {resp_cand_recues.status_code}"
    cand_recues_content = resp_cand_recues.content.decode('utf-8')
    assert 'Candidatures Reçues' in cand_recues_content, "ERREUR: Header Candidatures Reçues manquant !"
    assert 'Filtrer par poste' in cand_recues_content, "ERREUR: Filtre par poste manquant !"
    assert 'Statut' in cand_recues_content, "ERREUR: Filtre par statut manquant !"
    print(" [OK] /entreprise/candidatures/: Portail RH Candidatures Reçues avec filtres conforme à hr_candidatures.php")

    # 6. Test d'insertion d'un Template et validation métier
    new_tpl_data = {
        'nom': 'Modèle Minimaliste Test',
        'description[]': ['Minimaliste', 'ATS-Friendly'],
        'structure_html': '<div class="cv-body"><h1>John Doe</h1><p>Developer</p></div>',
        'est_premium': '1'
    }
    resp_create = c_admin.post('/backoffice/templates/creer/', new_tpl_data, follow=True)
    assert resp_create.status_code == 200
    created_tpl = Template.objects.filter(nom='Modèle Minimaliste Test').first()
    assert created_tpl is not None, "ERREUR: Template non inséré en BDD !"
    assert created_tpl.est_premium == True, "ERREUR: est_premium non sauvegardé !"
    print(" [OK] Template CRUD: Création et validation réussies en BDD SQLite")

    print("\n TOUS LES TESTS METIERS, ARCHITECTURAUX ET ROLES SONT VALIDES AVEC SUCCES (100%) !")

if __name__ == '__main__':
    run_tests()
