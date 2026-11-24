from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    landing, admin_dashboard, login_view, logout_view,
    backoffice_utilisateurs, backoffice_offres, backoffice_formations,
    backoffice_veille
)

from accounts.views import (
    utilisateur_create, utilisateur_update, utilisateur_delete, account_settings, profile_view
)

from cv_studio.views import (
    template_list_admin, template_create, template_update, template_delete
)

from jobs.views import (
    candidature_list, offre_create, offre_update, offre_delete,
    entreprise_posts, entreprise_candidatures
)

from training.views import (
    formation_create, formation_update, formation_delete
)

def inscription_candidat(request):
    """Inscription candidat répliquant le flux authentique de signup_candidat.php"""
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.contrib.auth.hashers import make_password
    from accounts.models import Utilisateur, Candidat, Profil
    from accounts.auth_helpers import login_user
    from datetime import datetime

    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        prenom = (request.POST.get('prenom') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = (request.POST.get('password') or '').strip()
        password_confirm = (request.POST.get('password_confirm') or '').strip()
        telephone = (request.POST.get('telephone') or '').strip()
        linkedin = (request.POST.get('linkedin') or '').strip()
        competences = (request.POST.get('competences') or '').strip()
        niveau_etudes = (request.POST.get('niveauEtudes') or request.POST.get('niveau_etudes') or '').strip()
        niveau = (request.POST.get('niveau') or '').strip()
        adresse = (request.POST.get('adresse') or '').strip()
        ville = (request.POST.get('ville') or '').strip()
        pays = (request.POST.get('pays') or '').strip()
        date_naissance_str = (request.POST.get('date_naissance') or '').strip()

        date_naissance = None
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                date_naissance = None

        if not (nom and prenom and email and password):
            messages.error(request, "Veuillez remplir tous les champs obligatoires (*).")
            return render(request, 'accounts/signup_candidat.html', {'form_data': request.POST})

        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'accounts/signup_candidat.html', {'form_data': request.POST})

        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, 'accounts/signup_candidat.html', {'form_data': request.POST})

        if Utilisateur.objects.filter(email__iexact=email).exists():
            messages.error(request, "Cette adresse email est déjà utilisée par un autre compte.")
            return render(request, 'accounts/signup_candidat.html', {'form_data': request.POST})

        user = Utilisateur.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=make_password(password),
            role='Candidat',
            telephone=telephone or None
        )
        Candidat.objects.create(
            utilisateur=user,
            competences=competences or None,
            niveau_etudes=niveau_etudes or None,
            niveau=niveau or None
        )
        Profil.objects.create(
            utilisateur=user,
            adresse=adresse or None,
            ville=ville or None,
            pays=pays or None,
            date_naissance=date_naissance,
            linkedin=linkedin or None
        )
        login_user(request, user)
        messages.success(request, f"Bienvenue {user.prenom} ! Votre compte candidat a été créé avec succès.")
        return redirect('jobs:offre_list')

    return render(request, 'accounts/signup_candidat.html')

urlpatterns = [
    # ── Vue Front (Frontoffice - Expérience Candidat / Public) ──
    path('', landing, name='landing'),
    path('front/', landing, name='front'),
    path('connexion/', login_view, name='login'),
    path('login/', login_view, name='login_alias'),
    path('deconnexion/', logout_view, name='logout'),
    path('logout/', logout_view, name='logout_alias'),
    path('inscription/', inscription_candidat, name='signup_candidat'),
    path('signup/', inscription_candidat, name='signup_alias'),
    path('parametres/', account_settings, name='account_settings'),
    path('settings/', account_settings, name='settings_alias'),
    path('profil/', profile_view, name='profile'),

    # ── Espace Entreprise (Portail RH authentique) ──
    path('entreprise/postes/', entreprise_posts, name='entreprise_posts'),
    path('entreprise/candidatures/', entreprise_candidatures, name='entreprise_candidatures'),

    # ── Vue Back (Backoffice - Expérience Administrateur avec Sidebar) ──
    path('backoffice/', admin_dashboard, name='backoffice'),
    path('dashboard/', admin_dashboard, name='dashboard'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/', admin_dashboard, name='home'),
    
    # Backoffice Utilisateurs & CRUD
    path('backoffice/utilisateurs/', backoffice_utilisateurs, name='backoffice_utilisateurs'),
    path('backoffice/utilisateurs/creer/', utilisateur_create, name='backoffice_utilisateur_create'),
    path('backoffice/utilisateurs/<int:pk>/modifier/', utilisateur_update, name='backoffice_utilisateur_update'),
    path('backoffice/utilisateurs/<int:pk>/supprimer/', utilisateur_delete, name='backoffice_utilisateur_delete'),

    # Backoffice Offres d'emploi & CRUD
    path('backoffice/offres/', backoffice_offres, name='backoffice_offres'),
    path('backoffice/offres/creer/', offre_create, name='backoffice_offre_create'),
    path('backoffice/offres/<int:pk>/modifier/', offre_update, name='backoffice_offre_update'),
    path('backoffice/offres/<int:pk>/supprimer/', offre_delete, name='backoffice_offre_delete'),

    # Backoffice Formations & CRUD
    path('backoffice/formations/', backoffice_formations, name='backoffice_formations'),
    path('backoffice/formations/creer/', formation_create, name='backoffice_formation_create'),
    path('backoffice/formations/<int:pk>/modifier/', formation_update, name='backoffice_formation_update'),
    path('backoffice/formations/<int:pk>/supprimer/', formation_delete, name='backoffice_formation_delete'),

    # Backoffice Templates CV & CRUD (Authentic PHP Port)
    path('backoffice/templates/', template_list_admin, name='backoffice_cv_templates'),
    path('backoffice/templates/creer/', template_create, name='backoffice_template_create'),
    path('backoffice/templates/<int:pk>/modifier/', template_update, name='backoffice_template_update'),
    path('backoffice/templates/<int:pk>/supprimer/', template_delete, name='backoffice_template_delete'),

    # Backoffice Veille Marché
    path('backoffice/veille/', backoffice_veille, name='backoffice_veille'),

    # Redirection de /admin/ vers le Backoffice Aptus authentique
    path('admin/', admin_dashboard, name='admin_home'),
    path('django-admin/', admin.site.urls),

    # ── Modules Métier Front ──
    path('utilisateurs/', include('accounts.urls')),
    path('offres/', include('jobs.urls')),
    path('candidatures/', candidature_list, name='candidature_direct'),
    path('cv-studio/', include('cv_studio.urls')),
    path('formations/', include('training.urls')),
    path('marche/', include('market.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
