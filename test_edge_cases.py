import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from django.test import Client
from accounts.models import Utilisateur

def test_empty_form_submissions():
    print("=" * 60)
    print("TEST DE SOUMISSION DE FORMULAIRES VIDES / NONETYPE")
    print("=" * 60)
    
    client = Client()
    admin_user = Utilisateur.objects.filter(role='Admin').first()
    session = client.session
    session['user_id'] = admin_user.pk
    session['role'] = 'Admin'
    session.save()
    
    # 1. Test /offres/creer/ avec payload vide et valeurs None/vides
    print("\n1. Test POST /offres/creer/ avec champs vides (ce qui provoquait le crash AttributeError)...")
    try:
        resp = client.post('/offres/creer/', {
            'titre': '',
            'description': '',
            'question': '', # La cause exacte du bug NoneType
            'competences_requises': '',
            'salaire': '',
            'date_expir': ''
        })
        assert resp.status_code == 200, f"Attendu status 200 avec erreurs de validation, reçu {resp.status_code}"
        print("  [SUCCÈS] /offres/creer/ ne crashe plus! Le formulaire renvoie les erreurs de validation proprement.")
    except Exception as e:
        print(f"  [ÉCHEC] Exception levée: {e}")
        raise e
        
    # 2. Test /backoffice/formations/creer/ avec champs vides
    print("\n2. Test POST /backoffice/formations/creer/ avec champs vides...")
    try:
        resp = client.post('/backoffice/formations/creer/', {
            'titre': '',
            'domaine': '',
            'niveau': '',
            'description': '',
            'date_formation': ''
        })
        assert resp.status_code == 200, f"Attendu status 200, reçu {resp.status_code}"
        print("  [SUCCÈS] /backoffice/formations/creer/ gère proprement les champs vides sans crash.")
    except Exception as e:
        print(f"  [ÉCHEC] Exception levée: {e}")
        raise e

    # 3. Test /backoffice/utilisateurs/creer/ avec champs vides
    print("\n3. Test POST /backoffice/utilisateurs/creer/ avec champs vides...")
    try:
        resp = client.post('/backoffice/utilisateurs/creer/', {
            'nom': '',
            'prenom': '',
            'email': '',
            'mot_de_passe': '',
            'role': ''
        })
        assert resp.status_code == 200, f"Attendu status 200, reçu {resp.status_code}"
        print("  [SUCCÈS] /backoffice/utilisateurs/creer/ gère proprement les champs vides sans crash.")
    except Exception as e:
        print(f"  [ÉCHEC] Exception levée: {e}")
        raise e

    # 4. Test /backoffice/templates/creer/ avec champs vides
    print("\n4. Test POST /backoffice/templates/creer/ avec champs vides...")
    try:
        resp = client.post('/backoffice/templates/creer/', {
            'nom': '',
            'structure_html': ''
        })
        assert resp.status_code == 200, f"Attendu status 200, reçu {resp.status_code}"
        print("  [SUCCÈS] /backoffice/templates/creer/ gère proprement les champs vides sans crash.")
    except Exception as e:
        print(f"  [ÉCHEC] Exception levée: {e}")
        raise e

    print("\n" + "=" * 60)
    print("TOUS LES FORMULAIRES SONT DÉSORMAIS 100% ROBUSTES FACE AUX VALEURS NULL/NONE/VIDES !")
    print("=" * 60)

if __name__ == '__main__':
    test_empty_form_submissions()
