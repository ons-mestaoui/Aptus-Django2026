import os
import django
import sys
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from django.test import Client
from accounts.models import Utilisateur, Candidat, Entreprise
from jobs.models import OffreEmploi, Candidature
from training.models import Formation, Inscription
from cv_studio.models import Template

def run_tests():
    print("=" * 60)
    print("DEMARRAGE DES TESTS CRUD & REGLES METIER APTUS BACKOFFICE")
    print("=" * 60)
    
    client = Client()
    
    # 0. S'assurer qu'un compte admin existe et simuler sa session
    admin_user = Utilisateur.objects.filter(role='Admin').first()
    if not admin_user:
        admin_user = Utilisateur.objects.create(
            nom='SuperAdmin', prenom='Aptus', email='admin.test@aptus.com',
            mot_de_passe='AdminPass123!', role='Admin'
        )
    session = client.session
    session['user_id'] = admin_user.pk
    session['role'] = 'Admin'
    session['user_name'] = f"{admin_user.prenom} {admin_user.nom}"
    session.save()
    
    # S'assurer qu'une entreprise existe
    ent_user = Utilisateur.objects.filter(role='Entreprise').first()
    if not ent_user:
        ent_user = Utilisateur.objects.create(
            nom='EntrepriseTest', prenom='HR', email='hr.test@techcorp.com',
            mot_de_passe='Pass123456!', role='Entreprise'
        )
    entreprise, _ = Entreprise.objects.get_or_create(
        utilisateur=ent_user,
        defaults={'raison_sociale': 'TechCorp Solutions', 'secteur': 'Informatique'}
    )
    
    # ════════════════════════════════════════════════════════════════
    # 1. TEST FORMATIONS CRUD & CONTRAINTES
    # ════════════════════════════════════════════════════════════════
    print("\n--- 1. TEST FORMATIONS CRUD & CONTRAINTES ---")
    future_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M')
    past_date = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
    
    # Test contrainte date passée: doit échouer
    resp = client.post('/backoffice/formations/creer/', {
        'titre': 'Formation Passée Invalide',
        'domaine': 'Data Science',
        'niveau': 'Débutant',
        'description': 'Description du cours de test avec assez de contenu.',
        'date_formation': past_date,
    })
    assert Formation.objects.filter(titre='Formation Passée Invalide').count() == 0, "ERREUR: La date passée aurait dû être rejetée!"
    print("  [OK] Contrainte date_formation >= now() vérifiée avec succès (rejetée comme prévu).")
    
    # Test Création valide
    resp = client.post('/backoffice/formations/creer/', {
        'titre': 'Formation Test Automated',
        'domaine': 'Intelligence Artificielle',
        'niveau': 'Intermédiaire',
        'description': 'Description complète du programme de formation test.',
        'date_formation': future_date,
        'is_online': 'on',
        'lien_api_room': 'https://meet.jit.si/aptus-test-room-123'
    }, follow=True)
    f = Formation.objects.filter(titre='Formation Test Automated').first()
    assert f is not None, "ERREUR: Création de formation échouée!"
    print(f"  [OK] Formation créée avec succès: #{f.pk} - {f.titre}")
    
    # Test Modification (Update)
    resp = client.post(f'/backoffice/formations/{f.pk}/modifier/', {
        'titre': 'Formation Test Modifiée avec Succès',
        'domaine': 'Data & IA Avancée',
        'niveau': 'Avancé',
        'description': 'Description mise à jour avec nouveaux objectifs.',
        'date_formation': (timezone.now() + timedelta(days=15)).strftime('%Y-%m-%dT%H:%M'),
        'is_online': 'on',
        'lien_api_room': 'https://meet.jit.si/aptus-updated'
    }, follow=True)
    f.refresh_from_db()
    assert f.titre == 'Formation Test Modifiée avec Succès', "ERREUR: Modification formation échouée!"
    assert f.niveau == 'Avancé', "ERREUR: Niveau formation non mis à jour!"
    print(f"  [OK] Formation #{f.pk} modifiée avec succès: {f.titre}")
    
    # Test Inscription d'un candidat: progression à 0%
    cand_user, _ = Utilisateur.objects.get_or_create(
        email='cand.regle@aptus.test',
        defaults={'nom': 'Testeur', 'prenom': 'Jean', 'mot_de_passe': 'Pass123456!', 'role': 'Candidat'}
    )
    candidat, _ = Candidat.objects.get_or_create(utilisateur=cand_user)
    
    # Inscription
    session_cand = client.session
    session_cand['user_id'] = cand_user.pk
    session_cand['role'] = 'Candidat'
    session_cand.save()
    resp = client.get(f'/formations/{f.pk}/sinscrire/', follow=True)
    insc = Inscription.objects.filter(candidat=candidat, formation=f).first()
    assert insc is not None, "ERREUR: Inscription candidat échouée!"
    assert insc.progression == 0, f"ERREUR: La progression initiale doit être 0, obtenu: {insc.progression}"
    assert insc.statut == 'En attente', f"ERREUR: Le statut initial doit être 'En attente', obtenu: {insc.statut}"
    print(f"  [OK] Règle Métier Inscription: progression={insc.progression}%, statut='{insc.statut}' vérifiés.")
    
    # Test Suppression (Delete)
    # Re-connecter en tant qu'admin
    session['user_id'] = admin_user.pk
    session['role'] = 'Admin'
    session.save()
    resp = client.post(f'/backoffice/formations/{f.pk}/supprimer/', follow=True)
    assert not Formation.objects.filter(pk=f.pk).exists(), "ERREUR: Suppression formation échouée!"
    print(f"  [OK] Formation #{f.pk} supprimée avec succès du Backoffice.")
    
    # ════════════════════════════════════════════════════════════════
    # 2. TEST OFFRES D'EMPLOI CRUD & CONTRAINTES
    # ════════════════════════════════════════════════════════════════
    print("\n--- 2. TEST OFFRES D'EMPLOI CRUD & CONTRAINTES ---")
    future_expir = (date.today() + timedelta(days=30)).isoformat()
    past_expir = (date.today() - timedelta(days=5)).isoformat()
    
    # Test contrainte date expiration passée
    resp = client.post('/backoffice/offres/creer/', {
        'entreprise': entreprise.pk,
        'titre': 'Offre Expiree Invalide',
        'domaine': 'Web Dev',
        'salaire': 45000,
        'experience_requise': '2 ans',
        'description': 'Description du poste de test.',
        'question': 'Pourquoi vous ?',
        'date_expir': past_expir
    })
    assert OffreEmploi.objects.filter(titre='Offre Expiree Invalide').count() == 0, "ERREUR: L'offre avec date expirée aurait dû être rejetée!"
    print("  [OK] Contrainte date_expir >= today() vérifiée avec succès (rejetée comme prévu).")
    
    # Test Création valide
    resp = client.post('/backoffice/offres/creer/', {
        'entreprise': entreprise.pk,
        'titre': 'Développeur Fullstack Django / React',
        'domaine': 'Ingénierie Logicielle',
        'salaire': 55000,
        'experience_requise': '3 ans',
        'description': 'Conception et maintenance de plateformes scalables avec Python et React.',
        'competences_requises': 'Python, Django, JavaScript, React, PostgreSQL',
        'question': 'Avez-vous déjà déployé une app Django en production ?',
        'date_expir': future_expir
    }, follow=True)
    offre = OffreEmploi.objects.filter(titre='Développeur Fullstack Django / React').first()
    assert offre is not None, "ERREUR: Création offre d'emploi échouée!"
    print(f"  [OK] Offre créée avec succès: #{offre.pk} - {offre.titre}")
    
    # Test Modification (Update)
    resp = client.post(f'/backoffice/offres/{offre.pk}/modifier/', {
        'entreprise': entreprise.pk,
        'titre': 'Lead Architecte Django & Cloud',
        'domaine': 'Architecture Cloud',
        'salaire': 75000,
        'experience_requise': '5+ ans',
        'description': 'Direction technique des projets cloud et API REST.',
        'competences_requises': 'Django, Docker, Kubernetes, AWS',
        'question': 'Expérience avec Kubernetes ?',
        'date_expir': future_expir
    }, follow=True)
    offre.refresh_from_db()
    assert offre.titre == 'Lead Architecte Django & Cloud', "ERREUR: Titre de l'offre non mis à jour!"
    assert offre.salaire == 75000, "ERREUR: Salaire de l'offre non mis à jour!"
    print(f"  [OK] Offre #{offre.pk} modifiée avec succès: {offre.titre} (Salaire: {offre.salaire}€)")
    
    # Test Suppression (Delete)
    resp = client.post(f'/backoffice/offres/{offre.pk}/supprimer/', follow=True)
    assert not OffreEmploi.objects.filter(pk=offre.pk).exists(), "ERREUR: Suppression de l'offre échouée!"
    print(f"  [OK] Offre #{offre.pk} supprimée avec succès du Backoffice.")
    
    # ════════════════════════════════════════════════════════════════
    # 3. TEST UTILISATEURS CRUD & REGLES DE SECURITE
    # ════════════════════════════════════════════════════════════════
    print("\n--- 3. TEST UTILISATEURS CRUD & REGLES DE SECURITE ---")
    
    # Test Création d'un nouvel utilisateur
    resp = client.post('/backoffice/utilisateurs/creer/', {
        'prenom': 'Karim',
        'nom': 'Ben Salah',
        'email': 'karim.bensalah.test@aptus.com',
        'mot_de_passe': 'SecurePassword123!',
        'role': 'Candidat',
        'telephone': '+216 98 123 456'
    }, follow=True)
    new_user = Utilisateur.objects.filter(email='karim.bensalah.test@aptus.com').first()
    assert new_user is not None, "ERREUR: Création utilisateur échouée!"
    # Vérifier que le profil Candidat a été automatiquement créé
    assert Candidat.objects.filter(utilisateur=new_user).exists(), "ERREUR: Profil Candidat non généré automatiquement!"
    print(f"  [OK] Utilisateur créé avec succès: #{new_user.pk} - {new_user.prenom} {new_user.nom} (Rôle: {new_user.role})")
    
    # Test Modification (sans changer le mot de passe, doit préserver l'ancien mot de passe)
    old_pwd = new_user.mot_de_passe
    resp = client.post(f'/backoffice/utilisateurs/{new_user.pk}/modifier/', {
        'prenom': 'Karim',
        'nom': 'Ben Salah Updated',
        'email': 'karim.bensalah.test@aptus.com',
        'mot_de_passe': '', # VIDE = conserver ancien mot de passe
        'role': 'Tuteur',
        'telephone': '+216 22 999 888'
    }, follow=True)
    new_user.refresh_from_db()
    assert new_user.nom == 'Ben Salah Updated', "ERREUR: Nom non mis à jour!"
    assert new_user.mot_de_passe == old_pwd, "ERREUR: L'ancien mot de passe a été écrasé!"
    assert new_user.role == 'Tuteur', "ERREUR: Rôle non mis à jour!"
    print(f"  [OK] Utilisateur #{new_user.pk} mis à jour avec succès (Mot de passe préservé, rôle -> {new_user.role}).")
    
    # Test Protection Auto-Suppression: un admin connecté ne peut pas supprimer son propre compte
    resp = client.post(f'/backoffice/utilisateurs/{admin_user.pk}/supprimer/', follow=True)
    assert Utilisateur.objects.filter(pk=admin_user.pk).exists(), "ERREUR: L'admin connecté a pu supprimer son propre compte!"
    print("  [OK] Protection auto-suppression vérifiée (L'admin ne peut pas se supprimer lui-même).")
    
    # Test Suppression de l'utilisateur de test
    resp = client.post(f'/backoffice/utilisateurs/{new_user.pk}/supprimer/', follow=True)
    assert not Utilisateur.objects.filter(pk=new_user.pk).exists(), "ERREUR: Suppression utilisateur échouée!"
    print(f"  [OK] Utilisateur #{new_user.pk} supprimé avec succès.")
    
    # ════════════════════════════════════════════════════════════════
    # 4. TEST TEMPLATES CV CRUD
    # ════════════════════════════════════════════════════════════════
    print("\n--- 4. TEST TEMPLATES CV CRUD ---")
    
    # Test Création
    resp = client.post('/backoffice/templates/creer/', {
        'nom': 'Template Minimaliste Test',
        'description[]': ['Minimaliste', 'Professionnel', 'Technologie'],
        'structure_html': '<div class="cv-minimal"><h1>{{ nom }}</h1><p>{{ bio }}</p></div>',
        'est_premium': 'on'
    }, follow=True)
    tpl = Template.objects.filter(nom='Template Minimaliste Test').first()
    assert tpl is not None, "ERREUR: Création template CV échouée!"
    assert tpl.est_premium is True, "ERREUR: Statut VIP du template non activé!"
    print(f"  [OK] Template CV créé avec succès: #{tpl.pk} - {tpl.nom} (VIP: {tpl.est_premium})")
    
    # Test Modification (Update)
    resp = client.post(f'/backoffice/templates/{tpl.pk}/modifier/', {
        'nom': 'Template Minimaliste 2.0 Pro',
        'description[]': ['Épuré', 'ATS-Friendly'],
        'structure_html': '<div class="cv-minimal-2"><h1>{{ nom }}</h1><hr><p>{{ competences }}</p></div>',
        'est_premium': ''
    }, follow=True)
    tpl.refresh_from_db()
    assert tpl.nom == 'Template Minimaliste 2.0 Pro', "ERREUR: Nom template non mis à jour!"
    assert 'ATS-Friendly' in tpl.description, "ERREUR: Tags du template non mis à jour!"
    print(f"  [OK] Template CV #{tpl.pk} modifié avec succès: {tpl.nom}")
    
    # Test Suppression (Delete)
    resp = client.post(f'/backoffice/templates/{tpl.pk}/supprimer/', follow=True)
    assert not Template.objects.filter(pk=tpl.pk).exists(), "ERREUR: Suppression template CV échouée!"
    print(f"  [OK] Template CV #{tpl.pk} supprimé avec succès.")
    
    print("\n" + "=" * 60)
    print("TOUS LES TESTS DU BACKOFFICE APTUS ONT REUSSI A 100% !")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
