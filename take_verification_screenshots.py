import os
import time
from playwright.sync_api import sync_playwright

output_dir = r"C:\xampp\htdocs\aptus_django\screenshots_verification"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1600, 'height': 900})
    page = context.new_page()

    print("1. Connexion en tant qu'administrateur via ?demo=admin...")
    page.goto("http://127.0.0.1:8000/connexion/?demo=admin")
    page.wait_for_timeout(1000)

    print("2. Capture de /backoffice/formations/ avec Modale Centrée...")
    page.goto("http://127.0.0.1:8000/backoffice/formations/")
    page.wait_for_timeout(1000)
    page.click('button:has-text("Ajouter une formation")')
    page.wait_for_timeout(600)
    page.screenshot(path=os.path.join(output_dir, "01_formation_modal_centered.png"))
    print("  -> Sauvegardé: 01_formation_modal_centered.png")

    print("3. Capture de /backoffice/formations/creer/ (Formulaire 2 colonnes)...")
    page.goto("http://127.0.0.1:8000/backoffice/formations/creer/")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(output_dir, "02_formation_form_clean.png"))
    print("  -> Sauvegardé: 02_formation_form_clean.png")

    print("4. Capture de /backoffice/templates/creer/...")
    page.goto("http://127.0.0.1:8000/backoffice/templates/creer/")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(output_dir, "03_template_cv_form.png"))
    print("  -> Sauvegardé: 03_template_cv_form.png")

    print("5. Connexion en tant qu'Entreprise via ?demo=entreprise...")
    page.goto("http://127.0.0.1:8000/connexion/?demo=entreprise")
    page.wait_for_timeout(1000)

    print("6. Capture de /offres/creer/ pour Entreprise (Vue Front sans Sidebar)...")
    page.goto("http://127.0.0.1:8000/offres/creer/")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(output_dir, "04_entreprise_offre_form_front.png"))
    print("  -> Sauvegardé: 04_entreprise_offre_form_front.png")

    print("7. Connexion en tant que Candidat via ?demo=candidat...")
    page.goto("http://127.0.0.1:8000/connexion/?demo=candidat")
    page.wait_for_timeout(1000)

    print("8. Capture de SweetAlert2 sur Candidatures...")
    page.goto("http://127.0.0.1:8000/candidatures/")
    page.wait_for_timeout(1000)
    trash_btn = page.query_selector('a[title="Retirer ma candidature"]')
    if trash_btn:
        trash_btn.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(output_dir, "05_sweetalert_confirm_candidature.png"))
        print("  -> Sauvegardé: 05_sweetalert_confirm_candidature.png")
    else:
        page.screenshot(path=os.path.join(output_dir, "05_candidatures_list.png"))
        print("  -> Sauvegardé: 05_candidatures_list.png")

    browser.close()
    print("Captures terminées avec succès !")
