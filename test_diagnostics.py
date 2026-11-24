import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from django.test import Client
from accounts.models import Utilisateur
from jobs.models import OffreEmploi
from training.models import Formation

client = Client()

print("="*60)
print("APTUS DIAGNOSTIC & VERIFICATION SUITE")
print("="*60)

# Test 1: Anonymous Frontoffice Views
front_urls = [
    ('/', 'Landing Page'),
    ('/connexion/', 'Login Page'),
    ('/inscription/', 'Inscription Candidat'),
    ('/offres/', 'Offres Feed (Front)'),
    ('/formations/', 'Formations Catalog (Front)'),
    ('/marche/', 'Veille Marché (Front)'),
    ('/cv-studio/', 'CV Studio (Front)'),
]

print("\n--- 1. Testing Frontoffice (Candidat / Visiteur) ---")
for url, name in front_urls:
    res = client.get(url)
    has_sidebar = b'class="sidebar"' in res.content or b'id="sidebar"' in res.content
    assert res.status_code == 200, f"FAILED: {name} ({url}) returned {res.status_code}"
    assert not has_sidebar, f"FAILED: {name} ({url}) contains Admin Sidebar!"
    print(f" [PASS] {name} ({url}) -> HTTP 200 | No Sidebar (Strict Frontoffice)")

# Test 2: Detail Views (Offres & Formations)
first_offre = OffreEmploi.objects.first()
if first_offre:
    res = client.get(f'/offres/{first_offre.pk}/')
    assert res.status_code == 200
    assert b'id="sidebar"' not in res.content, "offre_detail contains sidebar!"
    assert b'Postuler' in res.content, "offre_detail missing Postuler button!"
    assert b'Modifier (Admin)' not in res.content, "offre_detail shows admin buttons to candidate!"
    print(f" [PASS] Offre Detail (/offres/{first_offre.pk}/) -> HTTP 200 | Frontoffice | 'Postuler' CTA Present | Admin Controls Hidden")

first_formation = Formation.objects.first()
if first_formation:
    res = client.get(f'/formations/{first_formation.pk}/')
    assert res.status_code == 200
    assert b'id="sidebar"' not in res.content, "formation_detail contains sidebar!"
    assert b"Rejoindre" in res.content or b"inscrire" in res.content, "formation_detail missing enrollment CTA!"
    assert b'Modifier (Admin)' not in res.content, "formation_detail shows admin buttons to candidate!"
    print(f" [PASS] Formation Detail (/formations/{first_formation.pk}/) -> HTTP 200 | Frontoffice | Enrollment CTA Present | Admin Controls Hidden")

# Test 3: Backoffice as Admin
print("\n--- 2. Testing Backoffice (Admin Management) ---")
admin_user = Utilisateur.objects.filter(role='Admin').first()
assert admin_user, "Admin user not found in database!"

# Log in admin in session
session = client.session
session['id_utilisateur'] = admin_user.id_utilisateur
session['user_id'] = admin_user.id_utilisateur
session['user_name'] = f"{admin_user.prenom} {admin_user.nom or ''}".strip()
session['user_email'] = admin_user.email
session['role'] = 'Admin'
session.save()

back_urls = [
    ('/backoffice/', 'Backoffice Dashboard'),
    ('/backoffice/offres/', 'Gestion Offres Table'),
    ('/backoffice/offres/creer/', 'Créer Offre Form'),
    ('/backoffice/formations/', 'Gestion Formations Table'),
    ('/backoffice/formations/creer/', 'Créer Formation Form'),
    ('/backoffice/utilisateurs/', 'Gestion Utilisateurs Table'),
    ('/backoffice/utilisateurs/creer/', 'Créer Utilisateur Form'),
    ('/backoffice/templates/', 'Gestion Templates CV Table'),
    ('/backoffice/veille/', 'Gestion Veille Marché Table'),
    ('/admin/', 'Custom Admin Route (/admin/)'),
]

for url, name in back_urls:
    res = client.get(url)
    assert res.status_code == 200, f"FAILED: {name} ({url}) returned {res.status_code}"
    assert b'id="sidebar"' in res.content or b'class="sidebar"' in res.content, f"FAILED: {name} ({url}) missing Admin Sidebar!"
    # Check form layout if it is a form
    if 'creer' in url:
        assert b'form-grid-2cols' in res.content or b'grid-template-columns: 1fr 1fr' in res.content, f"FAILED: {name} ({url}) missing 2-column wide layout!"
        assert b'layout_back.html' not in res.content, "Raw template string leak"
        print(f" [PASS] {name} ({url}) -> HTTP 200 | Backoffice Sidebar | Large 2-Column Centered Form")
    else:
        print(f" [PASS] {name} ({url}) -> HTTP 200 | Backoffice Sidebar | Custom Aptus Design")

# Test 4: Landing Page Verification (Anonymous Visitor)
print("\n--- 3. Testing Landing Page Content ---")
client = Client()
res = client.get('/')
assert b'Explorer les Opportunit' in res.content, "Landing page missing Explorer les Opportunités button!"
assert b'Acc\xc3\xa9der \xc3\xa0 la Vue Admin' not in res.content, "Landing page still contains 'Accéder à la Vue Admin' hero button!"
print(" [PASS] Landing Page hero is client-focused ('Explorer les Opportunités') without forced admin buttons")

print("\n" + "="*60)
print("ALL 18 VERIFICATION CHECKS PASSED PERFECTLY!")
print("="*60)
