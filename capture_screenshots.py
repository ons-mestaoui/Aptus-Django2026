import asyncio
from playwright.async_api import async_playwright

output_dir = r"C:\Users\outheila\.gemini\antigravity-cli\brain\f892950a-0292-4d03-803a-9b6a506cc252"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        # 1. Login as Jean Dupont (Candidat)
        await page.goto("http://127.0.0.1:8000/connexion/")
        await page.fill("input[name='email']", "jean.dupont@email.com")
        await page.fill("input[name='password']", "pass123")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        # Screenshot 1: Account Settings (Confidentialité Tab - Image 4 port)
        await page.goto("http://127.0.0.1:8000/parametres/?tab=privacy")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=f"{output_dir}/06_parametres_confidentialite.png", full_page=True)
        print("Captured 06_parametres_confidentialite.png")

        # Screenshot 2: Suivi des candidatures (Clean, no static banner, no duplicate offers)
        await page.goto("http://127.0.0.1:8000/candidatures/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=f"{output_dir}/07_suivi_candidatures_clean.png", full_page=True)
        print("Captured 07_suivi_candidatures_clean.png")

        # Screenshot 3: Mes Formations as Candidat (Progression starting at 0% with no duplicate static banner)
        await page.goto("http://127.0.0.1:8000/formations/mes-formations/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=f"{output_dir}/08_mes_formations_0_percent.png", full_page=True)
        print("Captured 08_mes_formations_0_percent.png")

        # 2. Login as Marc Lemoine (Tuteur)
        await page.goto("http://127.0.0.1:8000/deconnexion/")
        await page.wait_for_load_state("networkidle")
        await page.goto("http://127.0.0.1:8000/connexion/")
        await page.fill("input[name='email']", "tuteur.marc@email.com")
        await page.fill("input[name='password']", "pass123")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        # Screenshot 4: Tuteur View (Teacher View & Tuteur Navbar)
        await page.goto("http://127.0.0.1:8000/formations/mes-formations/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=f"{output_dir}/09_tuteur_espace_formateur.png", full_page=True)
        print("Captured 09_tuteur_espace_formateur.png")

        await browser.close()

asyncio.run(main())
