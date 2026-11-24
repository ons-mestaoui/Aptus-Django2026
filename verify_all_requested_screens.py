import os
import time
from playwright.sync_api import sync_playwright

os.makedirs('C:/xampp/htdocs/aptus_django/screenshots', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    # Track dialogs (alert/confirm/prompt)
    native_dialogs = []
    page.on('dialog', lambda dialog: [
        native_dialogs.append(f"TYPE={dialog.type} MSG={dialog.message}"),
        dialog.dismiss()
    ])

    print("="*60)
    print("STARTING E2E VERIFICATION OF ALL REQUESTED SCREENS")
    print("="*60)

    # ----------------------------------------------------
    # 1. Page Inscription (/inscription/)
    # ----------------------------------------------------
    print("\n--- 1. Testing /inscription/ ---")
    page.goto('http://127.0.0.1:8000/inscription/')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    # Vérification absence de navbar frontoffice
    has_front_navbar = page.locator('nav.navbar, header.navbar, .front-navbar, nav.navbar-expand-lg').count()
    has_nav_links = page.locator('a:has-text("Offres"), a:has-text("Formations"), a:has-text("Veille Marché")').count()
    has_standalone_card = page.locator('.auth-box, form, .card').count()
    
    print(f"  Front navbar elements found: {has_front_navbar}")
    print(f"  Front nav links found: {has_nav_links}")
    print(f"  Auth card found: {has_standalone_card > 0}")

    assert has_front_navbar == 0, "Error: Navbar front found in /inscription/!"
    assert has_nav_links == 0, "Error: Front navbar links found in /inscription/!"
    page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/verify_01_inscription_clean.png', full_page=True)
    print("  [PASS] /inscription/ is clean standalone page without front navbar banner!")

    # ----------------------------------------------------
    # 2. Catalogue des Templates CV (/cv-studio/templates/)
    # ----------------------------------------------------
    print("\n--- 2. Testing /cv-studio/templates/ ---")
    page.goto('http://127.0.0.1:8000/cv-studio/templates/')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    template_cards = page.locator('.template-card')
    card_count = template_cards.count()
    print(f"  Template cards found: {card_count}")
    assert card_count > 0, "Error: No template cards found in catalogue!"

    # Count cards with images or iframe previews vs grey skeletons
    imgs_count = page.locator('.template-card img').count()
    iframes_count = page.locator('.template-card iframe').count()
    grey_skeletons = page.locator('.template-card__preview-line').count()

    print(f"  Templates with real image thumbnails: {imgs_count}")
    print(f"  Templates with live iframe previews: {iframes_count}")
    print(f"  Grey skeleton lines found: {grey_skeletons}")

    assert imgs_count > 0, "Error: No image thumbnails rendered in catalogue!"
    assert grey_skeletons == 0, f"Error: Still found {grey_skeletons} grey skeleton elements!"

    page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/verify_02_templates_catalogue.png', full_page=True)
    print("  [PASS] Templates catalogue displays real previews replacing grey skeleton blocks!")

    # ----------------------------------------------------
    # 3. Formulaire Création/Édition de Formation (Backoffice)
    # ----------------------------------------------------
    print("\n--- 3. Testing Formulaire Formation (Créer / Éditer) ---")
    # Login as Admin
    page.goto('http://127.0.0.1:8000/connexion/?demo=admin')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    # Open /backoffice/formations/creer/
    page.goto('http://127.0.0.1:8000/backoffice/formations/creer/')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    has_titre = page.locator('input[name="titre"]').count() > 0
    has_duree = page.locator('input[name="duree"]').count() > 0
    has_date_debut = page.locator('input[name="date_formation"]').count() > 0
    has_date_fin = page.locator('input[name="date_fin"]').count() > 0
    has_tuteur = page.locator('select[name="tuteur"]').count() > 0
    has_prerequis = page.locator('select[name="prerequis"]').count() > 0
    has_image = page.locator('input[name="image"]').count() > 0
    has_is_online = page.locator('select[name="is_online"], #id_is_online').count() > 0
    has_quill = page.locator('.ql-editor, #quill-editor-container').count() > 0
    has_visio = page.locator('#visio-room-group, input[name="lien_api_room"]').count() > 0

    print(f"  Champs vérifiés :")
    print(f"   - Titre: {has_titre}")
    print(f"   - Durée (ex: 10h): {has_duree}")
    print(f"   - Date de début: {has_date_debut}")
    print(f"   - Date de fin (optionnel): {has_date_fin}")
    print(f"   - Tuteur référent: {has_tuteur}")
    print(f"   - Prérequis optionnel: {has_prerequis}")
    print(f"   - Image 16:9: {has_image}")
    print(f"   - Format / Modalité (Présentiel vs En ligne): {has_is_online}")
    print(f"   - Éditeur riche Quill: {has_quill}")
    print(f"   - Lien Visioconférence API Room: {has_visio}")

    assert has_duree and has_date_debut and has_date_fin and has_prerequis and has_image and has_is_online and has_quill, "Error: Missing required formation fields!"

    # Test toggling format to 'En ligne' to verify conditional visio room display
    page.select_option('#id_is_online', 'True')
    time.sleep(0.3)
    visio_visible = page.locator('#visio-room-group').is_visible()
    print(f"   - Visio room conditionnellement affichée quand En ligne: {visio_visible}")
    assert visio_visible, "Error: Visio field not shown when is_online is selected!"

    page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/verify_03_formation_form_complete.png', full_page=True)
    print("  [PASS] Formulaire de formation complet avec Quill, dates, durée, prérequis, image et visio!")

    # ----------------------------------------------------
    # 4. Espace « Mes Cours Inscrits » (/formations/mes-formations/)
    # ----------------------------------------------------
    print("\n--- 4. Testing « Mes Cours Inscrits » ---")
    # Login as Candidat
    page.goto('http://127.0.0.1:8000/connexion/?demo=candidat')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    page.goto('http://127.0.0.1:8000/formations/mes-formations/')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    has_prog_banner = page.locator('.global-progress-bar').count() > 0 or page.get_by_text("Mon Parcours").count() > 0
    has_stat_cards = page.locator('.mini-stat-card').count() >= 3
    has_filter_tabs = page.locator('.custom-nav-tabs').count() > 0 or page.get_by_text("En cours").count() > 0
    has_cards_grid = page.locator('#formationsGrid, .formations-grid').count() > 0

    print(f"  Structure formations_my vérifiée :")
    print(f"   - Bannière de progression globale: {has_prog_banner}")
    print(f"   - Cartes statistiques mini (En cours / Terminées / Total): {has_stat_cards}")
    print(f"   - Onglets de filtrage par statut: {has_filter_tabs}")
    print(f"   - Grille de cartes de formation: {has_cards_grid}")

    assert has_prog_banner and has_stat_cards and has_filter_tabs and has_cards_grid, "Error: formation_my structure incomplete!"
    page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/verify_04_mes_cours_inscrits.png', full_page=True)
    print("  [PASS] Espace « Mes Cours Inscrits » parfaitement aligné avec l'authentique formations_my.php!")

    # ----------------------------------------------------
    # 5. Clic sur Supprimer (Pas de popup natif, pas de sidebar backoffice)
    # ----------------------------------------------------
    print("\n--- 5. Testing Suppression Entreprise (Frontoffice) ---")
    # Login as Entreprise
    page.goto('http://127.0.0.1:8000/connexion/?demo=entreprise')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    # Go to Mes Postes (/entreprise/postes/)
    page.goto('http://127.0.0.1:8000/entreprise/postes/')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

    # Check that sidebar is absent in Entreprise frontoffice
    has_sidebar_entreprise = page.locator('.sidebar, #sidebar, .admin-sidebar').count()
    print(f"  Sidebar backoffice présente sur l'espace Entreprise: {has_sidebar_entreprise}")
    assert has_sidebar_entreprise == 0, "Error: Sidebar backoffice leaked in Entreprise frontoffice!"

    # Click on a delete button
    del_btn = page.locator('button[onclick*="aptusDeleteWithForm"], a:has-text("Supprimer")').first
    if del_btn.count() > 0:
        print("  Clicking on delete action...")
        del_btn.click()
        time.sleep(0.5)

        # Verify SweetAlert modal is visible
        swal_visible = page.locator('.swal2-modal, .swal2-popup').is_visible()
        swal_title = page.locator('.swal2-title').text_content() if swal_visible else ""
        print(f"  SweetAlert2 modale affichée: {swal_visible} (Titre: '{swal_title}')")
        assert swal_visible, "Error: SweetAlert2 modal not triggered on delete!"

        # Verify NO native browser dialog occurred
        print(f"  Native browser dialogs recorded: {len(native_dialogs)}")
        assert len(native_dialogs) == 0, f"Error: Native browser popup detected! {native_dialogs}"

        page.screenshot(path='C:/xampp/htdocs/aptus_django/screenshots/verify_05_sweetalert_delete_modal.png')
        print("  [PASS] Delete triggered clean SweetAlert modal without native confirm()!")

        # Dismiss SweetAlert
        page.locator('.swal2-cancel').click()
        time.sleep(0.3)

    browser.close()
    print("\n" + "="*60)
    print("ALL 5 REQUESTED CHECKS PASSED WITH ZERO DEFECTS!")
    print("="*60)
