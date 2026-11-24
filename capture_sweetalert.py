import os
import django
from playwright.sync_api import sync_playwright

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from accounts.models import Utilisateur, Candidat
from jobs.models import OffreEmploi, Candidature

cand_user = Utilisateur.objects.filter(role='Candidat').first()
candidat, _ = Candidat.objects.get_or_create(utilisateur=cand_user)
offre = OffreEmploi.objects.first()

if not Candidature.objects.filter(candidat=candidat, offre=offre).exists():
    Candidature.objects.create(
        candidat=candidat,
        offre=offre,
        reponses_ques="Voici ma réponse de filtrage détaillée avec plus de dix caractères.",
        statut='en_attente',
        note=85
    )

output_dir = r"C:\Users\outheila\.gemini\antigravity-cli\brain\f892950a-0292-4d03-803a-9b6a506cc252"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 900})

    page.goto("http://127.0.0.1:8000/connexion/?demo=candidat")
    page.wait_for_timeout(1000)

    page.goto("http://127.0.0.1:8000/candidatures/")
    page.wait_for_timeout(1000)

    trash_btn = page.query_selector('a[title="Retirer ma candidature"]')
    if trash_btn:
        trash_btn.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(output_dir, "05_sweetalert_confirm_candidature.png"))
        print("SweetAlert2 capture réussie!")

    browser.close()
