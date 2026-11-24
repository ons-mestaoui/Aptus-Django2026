import os
import time
from playwright.sync_api import sync_playwright

output_dir = r"C:\xampp\htdocs\aptus_django\screenshots"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. Landing Page
    page.goto("http://127.0.0.1:8000/")
    time.sleep(1)
    page.screenshot(path=os.path.join(output_dir, "01_landing_fixed.png"))
    print("Captured 01_landing_fixed.png")

    # 2. Login as Admin
    page.goto("http://127.0.0.1:8000/connexion/?demo=admin")
    time.sleep(1)

    # 3. Form Créer Offre (Backoffice)
    page.goto("http://127.0.0.1:8000/backoffice/offres/creer/")
    time.sleep(1)
    page.screenshot(path=os.path.join(output_dir, "02_form_offre_large_centered.png"))
    print("Captured 02_form_offre_large_centered.png")

    # 4. Form Créer Formation (Backoffice)
    page.goto("http://127.0.0.1:8000/backoffice/formations/creer/")
    time.sleep(1)
    page.screenshot(path=os.path.join(output_dir, "03_form_formation_large_centered.png"))
    print("Captured 03_form_formation_large_centered.png")

    # 5. Detail Offre (Frontoffice)
    page.goto("http://127.0.0.1:8000/offres/1/")
    time.sleep(1)
    page.screenshot(path=os.path.join(output_dir, "04_offre_detail_frontoffice.png"))
    print("Captured 04_offre_detail_frontoffice.png")

    browser.close()
    print("Playwright screenshots completed successfully!")
