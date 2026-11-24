from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from accounts.auth_helpers import admin_required, check_user_password, logout_user
from .models import Utilisateur, Candidat, Entreprise, Administrateur, Profil
from .forms import UtilisateurForm, CandidatForm, EntrepriseForm, ProfilForm

@admin_required
def utilisateur_list(request):
    role_filter = (request.GET.get('role') or '').strip()
    query = (request.GET.get('q') or '').strip()
    sort = (request.GET.get('sort') or '').strip()
    order = (request.GET.get('order') or 'asc').strip().lower()
    
    users = Utilisateur.objects.select_related('profil').all()
    if role_filter:
        users = users.filter(role=role_filter)
    if query:
        users = users.filter(nom__icontains=query) | users.filter(prenom__icontains=query) | users.filter(email__icontains=query)
        
    if sort == 'nom':
        users = users.order_by('-nom' if order == 'desc' else 'nom')
    elif sort == 'email':
        users = users.order_by('-email' if order == 'desc' else 'email')
    elif sort == 'role':
        users = users.order_by('-role' if order == 'desc' else 'role')
    elif sort == 'id':
        users = users.order_by('-id_utilisateur' if order == 'desc' else 'id_utilisateur')
    else:
        users = users.order_by('-id_utilisateur')

    return render(request, 'accounts/utilisateur_list.html', {
        'users': users,
        'role_filter': role_filter,
        'query': query,
        'sort': sort,
        'order': order,
        'stats': {
            'total': Utilisateur.objects.count(),
            'candidats': Utilisateur.objects.filter(role='Candidat').count(),
            'entreprises': Utilisateur.objects.filter(role='Entreprise').count(),
            'tuteurs': Utilisateur.objects.filter(role__in=['Tuteur', 'Admin']).count(),
        }
    })

@admin_required
def utilisateur_detail(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)
    profil = Profil.objects.filter(utilisateur=user).first()
    candidat = Candidat.objects.filter(utilisateur=user).first()
    entreprise = Entreprise.objects.filter(utilisateur=user).first()
    return render(request, 'accounts/utilisateur_detail.html', {
        'user': user,
        'profil': profil,
        'candidat': candidat,
        'entreprise': entreprise
    })

@admin_required
def utilisateur_create(request):
    """Création d'un utilisateur avec formulaire complet Aptus (port de signup_candidat & users.php)."""
    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        prenom = (request.POST.get('prenom') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        password = (request.POST.get('mot_de_passe') or request.POST.get('motDePasse') or request.POST.get('password') or '').strip()
        password_confirm = (request.POST.get('password_confirm') or '').strip()
        role = (request.POST.get('role') or 'Candidat').strip()
        telephone = (request.POST.get('telephone') or '').strip()
        linkedin = (request.POST.get('linkedin') or '').strip()
        date_naissance_str = (request.POST.get('date_naissance') or request.POST.get('dateNaissance') or '').strip()
        pays = (request.POST.get('pays') or '').strip()
        ville = (request.POST.get('ville') or '').strip()
        adresse = (request.POST.get('adresse') or '').strip()
        competences = (request.POST.get('competences') or '').strip()
        niveau_etudes = (request.POST.get('niveau_etudes') or request.POST.get('niveauEtudes') or '').strip()
        niveau = (request.POST.get('niveau') or '').strip()
        raison_sociale = (request.POST.get('raison_sociale') or request.POST.get('raisonSociale') or '').strip()
        secteur = (request.POST.get('secteur') or '').strip()
        siret = (request.POST.get('siret') or '').strip()

        # Validation obligatoire
        if not (nom and prenom and email and password):
            messages.error(request, "Nom, prénom, email et mot de passe sont obligatoires.")
            return render(request, 'accounts/utilisateur_form.html', {
                'form_data': request.POST,
                'title': 'Créer un Utilisateur',
                'is_update': False
            })

        if password_confirm and password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'accounts/utilisateur_form.html', {
                'form_data': request.POST,
                'title': 'Créer un Utilisateur',
                'is_update': False
            })

        if len(password) < 8:
            messages.error(request, "Le mot de passe doit comporter au moins 8 caractères.")
            return render(request, 'accounts/utilisateur_form.html', {
                'form_data': request.POST,
                'title': 'Créer un Utilisateur',
                'is_update': False
            })

        if Utilisateur.objects.filter(email__iexact=email).exists():
            messages.error(request, f"L'adresse email '{email}' est déjà utilisée par un autre compte.")
            return render(request, 'accounts/utilisateur_form.html', {
                'form_data': request.POST,
                'title': 'Créer un Utilisateur',
                'is_update': False
            })

        date_naissance = None
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                date_naissance = None

        # 1. Insertion dans la table utilisateur
        user = Utilisateur.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=make_password(password),
            role=role,
            telephone=telephone or None
        )

        # 2. Insertion dans la table profil
        Profil.objects.create(
            utilisateur=user,
            adresse=adresse or None,
            ville=ville or None,
            pays=pays or None,
            date_naissance=date_naissance,
            linkedin=linkedin or None
        )

        # 3. Insertion selon le rôle
        if role == 'Candidat':
            Candidat.objects.create(
                utilisateur=user,
                competences=competences or None,
                niveau_etudes=niveau_etudes or None,
                niveau=niveau or None
            )
        elif role == 'Entreprise':
            Entreprise.objects.create(
                utilisateur=user,
                raison_sociale=raison_sociale or f"{prenom} {nom}",
                secteur=secteur or None,
                siret=siret or None
            )
        elif role == 'Admin':
            Administrateur.objects.create(
                utilisateur=user,
                niveau='Super Admin'
            )

        messages.success(request, f"Utilisateur {user.prenom} {user.nom or ''} ({user.role}) créé et enregistré dans la base de données !")
        return redirect('backoffice_utilisateurs')

    return render(request, 'accounts/utilisateur_form.html', {
        'title': 'Créer un Utilisateur',
        'is_update': False,
        'form_data': {},
        'user_obj': None,
    })

@admin_required
def utilisateur_update(request, pk):
    """Mise à jour d'un utilisateur et de son profil en base de données."""
    user = get_object_or_404(Utilisateur, pk=pk)
    profil, _ = Profil.objects.get_or_create(utilisateur=user)
    candidat = Candidat.objects.filter(utilisateur=user).first()
    entreprise = Entreprise.objects.filter(utilisateur=user).first()

    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        prenom = (request.POST.get('prenom') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        password = (request.POST.get('mot_de_passe') or request.POST.get('motDePasse') or request.POST.get('password') or '').strip()
        password_confirm = (request.POST.get('password_confirm') or '').strip()
        role = (request.POST.get('role') or user.role).strip()
        telephone = (request.POST.get('telephone') or '').strip()
        linkedin = (request.POST.get('linkedin') or '').strip()
        date_naissance_str = (request.POST.get('date_naissance') or request.POST.get('dateNaissance') or '').strip()
        pays = (request.POST.get('pays') or '').strip()
        ville = (request.POST.get('ville') or '').strip()
        adresse = (request.POST.get('adresse') or '').strip()
        competences = (request.POST.get('competences') or '').strip()
        niveau_etudes = (request.POST.get('niveau_etudes') or request.POST.get('niveauEtudes') or '').strip()
        niveau = (request.POST.get('niveau') or '').strip()
        raison_sociale = (request.POST.get('raison_sociale') or request.POST.get('raisonSociale') or '').strip()
        secteur = (request.POST.get('secteur') or '').strip()
        siret = (request.POST.get('siret') or '').strip()

        if not (nom and prenom and email):
            messages.error(request, "Nom, prénom et email sont obligatoires.")
            return render(request, 'accounts/utilisateur_form.html', {
                'user_obj': user,
                'profil': profil,
                'candidat': candidat,
                'entreprise': entreprise,
                'title': f'Modifier {user.prenom} {user.nom or ""}',
                'is_update': True
            })

        if Utilisateur.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            messages.error(request, f"L'adresse email '{email}' est déjà utilisée par un autre compte.")
            return render(request, 'accounts/utilisateur_form.html', {
                'user_obj': user,
                'profil': profil,
                'candidat': candidat,
                'entreprise': entreprise,
                'title': f'Modifier {user.prenom} {user.nom or ""}',
                'is_update': True
            })

        if password:
            if len(password) < 8:
                messages.error(request, "Le mot de passe doit comporter au moins 8 caractères.")
                return render(request, 'accounts/utilisateur_form.html', {
                    'user_obj': user,
                    'profil': profil,
                    'candidat': candidat,
                    'entreprise': entreprise,
                    'title': f'Modifier {user.prenom} {user.nom or ""}',
                    'is_update': True
                })
            if password_confirm and password != password_confirm:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return render(request, 'accounts/utilisateur_form.html', {
                    'user_obj': user,
                    'profil': profil,
                    'candidat': candidat,
                    'entreprise': entreprise,
                    'title': f'Modifier {user.prenom} {user.nom or ""}',
                    'is_update': True
                })
            user.mot_de_passe = make_password(password)

        user.nom = nom
        user.prenom = prenom
        user.email = email
        user.role = role
        user.telephone = telephone or None
        user.save()

        # Mise à jour du Profil
        if date_naissance_str:
            try:
                profil.date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        profil.linkedin = linkedin or None
        profil.pays = pays or None
        profil.ville = ville or None
        profil.adresse = adresse or None
        profil.save()

        # Mise à jour profil spécifique
        if role == 'Candidat':
            cand, _ = Candidat.objects.get_or_create(utilisateur=user)
            cand.competences = competences or None
            cand.niveau_etudes = niveau_etudes or None
            cand.niveau = niveau or None
            cand.save()
        elif role == 'Entreprise':
            ent, _ = Entreprise.objects.get_or_create(utilisateur=user)
            ent.raison_sociale = raison_sociale or f"{prenom} {nom}"
            ent.secteur = secteur or None
            ent.siret = siret or None
            ent.save()

        messages.success(request, f"Utilisateur {user.prenom} {user.nom or ''} mis à jour avec succès dans la base de données !")
        return redirect('backoffice_utilisateurs')

    return render(request, 'accounts/utilisateur_form.html', {
        'user_obj': user,
        'profil': profil,
        'candidat': candidat,
        'entreprise': entreprise,
        'form_data': {},
        'title': f'Modifier {user.prenom} {user.nom or ""}',
        'is_update': True
    })

@admin_required
def utilisateur_delete(request, pk):
    """Suppression définitive de l'utilisateur de la base de données (POST uniquement)."""
    user = get_object_or_404(Utilisateur, pk=pk)
    curr = request.session.get('user_id')
    if curr and curr == user.pk:
        messages.error(request, "Impossible de supprimer votre propre compte actuellement connecté.")
        return redirect('backoffice_utilisateurs')

    if request.method == 'POST':
        nom = f"{user.prenom} {user.nom or ''}"
        user.delete()
        messages.success(request, f"Utilisateur {nom} supprimé définitivement de la base de données !")
        return redirect('backoffice_utilisateurs')

    return render(request, 'accounts/utilisateur_confirm_delete.html', {'user': user})


def account_settings(request):
    """Portail Paramètres du Compte — Port fidèle de settings.php."""
    from accounts.auth_helpers import get_current_user
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour accéder aux paramètres.")
        return redirect('login')

    # Preferences stockées en session
    prefs = request.session.get('user_preferences', {})
    default_prefs = {
        'ai_assistant': False,
        'public_profile': True,
        'show_email': False,
        'show_phone': False,
        'recruiter_search': True,
        'language': 'fr',
        'timezone': 'Africa/Tunis',
        'theme': 'light',
        'accent_color': '#6B34A3',
        'font_family': 'Inter',
        'border_radius': 'medium',
        'notif_jobs': True,
        'notif_candidatures': True,
        'notif_formations': True,
    }
    for k, v in default_prefs.items():
        if k not in prefs:
            prefs[k] = v

    active_tab = request.GET.get('tab', 'general')

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        if action == 'update_privacy':
            active_tab = 'privacy'
            prefs['ai_assistant'] = bool(request.POST.get('ai_assistant'))
            prefs['public_profile'] = bool(request.POST.get('public_profile'))
            prefs['show_email'] = bool(request.POST.get('show_email'))
            prefs['show_phone'] = bool(request.POST.get('show_phone'))
            prefs['recruiter_search'] = bool(request.POST.get('recruiter_search'))
            request.session['user_preferences'] = prefs
            messages.success(request, "Paramètres de confidentialité enregistrés.")
            return redirect(f"{request.path}?tab=privacy")

        elif action == 'update_appearance':
            active_tab = 'appearance'
            prefs['theme'] = (request.POST.get('theme') or 'light').strip()
            prefs['accent_color'] = (request.POST.get('accent_color') or '#6B34A3').strip()
            prefs['font_family'] = (request.POST.get('font_family') or 'Inter').strip()
            prefs['border_radius'] = (request.POST.get('border_radius') or 'medium').strip()
            request.session['user_preferences'] = prefs
            messages.success(request, "Préférences d'apparence mises à jour.")
            return redirect(f"{request.path}?tab=appearance")

        elif action == 'update_general':
            active_tab = 'general'
            prefs['language'] = (request.POST.get('language') or 'fr').strip()
            prefs['timezone'] = (request.POST.get('timezone') or 'Africa/Tunis').strip()
            request.session['user_preferences'] = prefs
            messages.success(request, "Paramètres généraux enregistrés.")
            return redirect(f"{request.path}?tab=general")

        elif action == 'update_notifications':
            active_tab = 'notifications'
            prefs['notif_jobs'] = bool(request.POST.get('notif_jobs'))
            prefs['notif_candidatures'] = bool(request.POST.get('notif_candidatures'))
            prefs['notif_formations'] = bool(request.POST.get('notif_formations'))
            request.session['user_preferences'] = prefs
            messages.success(request, "Préférences de notifications enregistrées.")
            return redirect(f"{request.path}?tab=notifications")

        elif action == 'change_password':
            active_tab = 'security'
            current_pwd = (request.POST.get('current_password') or '').strip()
            new_pwd = (request.POST.get('new_password') or '').strip()
            confirm_pwd = (request.POST.get('confirm_password') or '').strip()

            if user.mot_de_passe and not check_user_password(current_pwd, user.mot_de_passe):
                messages.error(request, "Le mot de passe actuel est incorrect.")
            elif len(new_pwd) < 8:
                messages.error(request, "Le nouveau mot de passe doit comporter au moins 8 caractères.")
            elif new_pwd != confirm_pwd:
                messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            else:
                user.mot_de_passe = make_password(new_pwd)
                user.save(update_fields=['mot_de_passe'])
                messages.success(request, "Mot de passe mis à jour avec succès.")
            return redirect(f"{request.path}?tab=security")

        elif action == 'delete_account':
            active_tab = 'security'
            password_delete = (request.POST.get('password_delete') or '').strip()
            if not password_delete:
                messages.error(request, "Veuillez saisir votre mot de passe pour confirmer la suppression de votre compte.")
                return redirect(f"{request.path}?tab=security")

            if not check_user_password(password_delete, user.mot_de_passe):
                messages.error(request, "Mot de passe incorrect. La suppression du compte a été annulée.")
                return redirect(f"{request.path}?tab=security")

            # US 4.4: Suppression irréversible du compte et déconnexion
            user_name = f"{user.prenom} {user.nom or ''}".strip()
            user.delete()
            logout_user(request)
            messages.success(request, f"Votre compte ({user_name}) a été définitivement supprimé. Au revoir.")
            return redirect('landing')

    badges = [
        {'id': 1, 'nom': 'Pionnier Aptus', 'desc': 'Inscrit parmi les premiers utilisateurs de la plateforme', 'icon': 'award', 'unlocked': True, 'date': '2026'},
        {'id': 2, 'nom': 'Apprenant Assidu', 'desc': 'Participation active aux modules de formation', 'icon': 'book-open', 'unlocked': True, 'date': '2026'},
        {'id': 3, 'nom': 'Profil Optimisé', 'desc': 'Informations professionnelles et compétences complètes', 'icon': 'check-circle-2', 'unlocked': True, 'date': '2026'},
        {'id': 4, 'nom': 'Expert Technique', 'desc': 'Validation de parcours avancés et scoring prédictif élevé', 'icon': 'zap', 'unlocked': False, 'date': 'Verrouillé'},
    ]

    return render(request, 'accounts/settings.html', {
        'user': user,
        'prefs': prefs,
        'active_tab': active_tab,
        'badges': badges,
    })


def profile_view(request):
    """Frontoffice User Profile (port fidéle de profil_candidat.php et profil_entreprise.php)"""
    from accounts.auth_helpers import get_current_user
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour accéder à votre profil.")
        return redirect('login')

    profil, _ = Profil.objects.get_or_create(utilisateur=user)
    candidat = Candidat.objects.filter(utilisateur=user).first()
    entreprise = Entreprise.objects.filter(utilisateur=user).first()

    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        prenom = (request.POST.get('prenom') or '').strip()
        email = (request.POST.get('email') or '').strip()
        telephone = (request.POST.get('telephone') or '').strip()

        # Check email uniqueness if changed
        if email and email.lower() != user.email.lower() and Utilisateur.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            messages.error(request, "Cette adresse email est déjà utilisée par un autre compte.")
        else:
            if nom:
                user.nom = nom
            if prenom or user.role != 'Entreprise':
                user.prenom = prenom or user.prenom
            if email:
                user.email = email
            user.telephone = telephone or None
            user.save()
            request.session['user_name'] = f"{user.prenom} {user.nom or ''}".strip()
            request.session['user_email'] = user.email

            # Profile updates
            adresse = (request.POST.get('adresse') or '').strip()
            ville = (request.POST.get('ville') or '').strip()
            pays = (request.POST.get('pays') or '').strip()
            date_naissance_str = (request.POST.get('date_naissance') or '').strip()
            if date_naissance_str:
                from datetime import datetime
                try:
                    profil.date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            profil.adresse = adresse or None
            profil.ville = ville or None
            profil.pays = pays or None
            linkedin = (request.POST.get('linkedin') or '').strip()
            profil.linkedin = linkedin or None
            profil.save()

            # Candidat specific updates
            if user.role == 'Candidat':
                if not candidat:
                    candidat = Candidat.objects.create(utilisateur=user)
                candidat.competences = (request.POST.get('competences') or '').strip() or None
                candidat.niveau_etudes = (request.POST.get('niveauEtudes') or request.POST.get('niveau_etudes') or '').strip() or None
                candidat.niveau = (request.POST.get('niveau') or '').strip() or None
                candidat.save()

            # Entreprise specific updates
            elif user.role == 'Entreprise':
                if not entreprise:
                    entreprise = Entreprise.objects.create(utilisateur=user)
                entreprise.raison_sociale = nom or entreprise.raison_sociale
                entreprise.secteur = (request.POST.get('secteur') or '').strip() or None
                entreprise.siret = (request.POST.get('siret') or '').strip() or None
                entreprise.save()
                profil.site_web = (request.POST.get('site_web') or '').strip() or None
                profil.bio = (request.POST.get('bio') or '').strip() or None
                profil.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'user_obj': user,
        'profil': profil,
        'candidat': candidat,
        'entreprise': entreprise,
    })
