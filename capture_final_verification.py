import os
import time
from playwright.sync_api import sync_playwright

def capture():
    os.makedirs('C:/xampp/htdocs/aptus_django/screenshots', exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # 1. Capture offre_detail (Clean Front View - Candidate experience)
        print("Capturing 01_offre_detail_front_clean.png...")
        page.goto('http://127.0.0.1:8000/offres/1/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/01_offre_detail_front_clean.png', full_page=True)

        # 2. Login as Admin
        page.goto('http://127.0.0.1:8000/connexion/?demo=admin')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # 3. Capture Backoffice Template Form (matching uploaded_media_0_1795479099701.jpg)
        print("Capturing 02_backoffice_template_form.png...")
        page.goto('http://127.0.0.1:8000/backoffice/templates/creer/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/02_backoffice_template_form.png', full_page=True)

        # 4. Capture Backoffice Templates List
        print("Capturing 03_backoffice_templates_list.png...")
        page.goto('http://127.0.0.1:8000/backoffice/templates/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/03_backoffice_templates_list.png', full_page=True)

        # 5. Login as Entreprise
        page.goto('http://127.0.0.1:8000/connexion/?demo=entreprise')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # 6. Capture Entreprise Candidatures Reçues (matching uploaded_media_3_1795479099701.jpg)
        print("Capturing 04_entreprise_candidatures_recues.png...")
        page.goto('http://127.0.0.1:8000/entreprise/candidatures/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='C:/xampp\htdocs/aptus_django/screenshots/04_entreprise_candidatures_recues.png', full_page=True)

        # 7. Capture Entreprise Mes Postes (matching hr_posts.php)
        print("Capturing 05_entreprise_mes_postes.png...")
        page.goto('http://127.0.0.1:8000/entreprise/postes/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/05_entreprise_mes_postes.png', full_page=True)

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == '__main__':
    capture()
