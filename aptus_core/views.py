from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from accounts.models import Utilisateur
from jobs.models import OffreEmploi, Candidature
from jobs.forms import OffreEmploiForm
from cv_studio.models import CV, Template
from training.models import Formation, Inscription
from training.forms import FormationForm
from market.models import RapportMarche, ReferenceRapport

from accounts.auth_helpers import authenticate_user, login_user, logout_user, admin_required, candidat_required, get_current_user

def landing(request):
    user = get_current_user(request)
    if user and user.role == 'Admin':
        return redirect('backoffice')
    
    context = {
        'stats': {
            'users': Utilisateur.objects.count(),
            'offres': OffreEmploi.objects.count(),
            'candidatures': Candidature.objects.count(),
            'cvs': CV.objects.count(),
            'formations': Formation.objects.count(),
            'rapports': RapportMarche.objects.count(),
        },
        'featured_offres': OffreEmploi.objects.select_related('entreprise').order_by('-id_offre')[:4],
        'featured_formations': Formation.objects.order_by('-id_formation')[:4],
    }
    return render(request, 'landing.html', context)

@admin_required
def admin_dashboard(request):
    context = {
        'stats': {
            'users': Utilisateur.objects.count(),
            'offres': OffreEmploi.objects.count(),
            'candidatures': Candidature.objects.count(),
            'cvs': CV.objects.count(),
            'formations': Formation.objects.count(),
            'rapports': RapportMarche.objects.count(),
        },
        'recent_users': Utilisateur.objects.order_by('-id_utilisateur')[:5],
        'recent_offres': OffreEmploi.objects.select_related('entreprise').order_by('-id_offre')[:5],
    }
    return render(request, 'home.html', context)

def login_view(request):
    """Page de Connexion Split-Screen Aptus avec support Démo & Authentification par Rôle"""
    if settings.DEBUG and request.GET.get('demo'):
        demo_role = request.GET.get('demo', '').lower()
        if demo_role == 'admin':
            admin_user = Utilisateur.objects.filter(role='Admin').first()
            if admin_user:
                login_user(request, admin_user)
                messages.success(request, f"Connexion Démo réussie : Bienvenue {admin_user.prenom} (Admin)")
                return redirect('backoffice')
        elif demo_role == 'entreprise':
            ent_user = Utilisateur.objects.filter(role='Entreprise').first()
            if ent_user:
                login_user(request, ent_user)
                messages.success(request, f"Connexion Démo réussie : Bienvenue {ent_user.prenom} (Entreprise)")
                return redirect('entreprise_posts')
        elif demo_role == 'candidat':
            cand_user = Utilisateur.objects.filter(role='Candidat').first()
            if cand_user:
                login_user(request, cand_user)
                messages.success(request, f"Connexion Démo réussie : Bienvenue {cand_user.prenom} (Candidat)")
                return redirect('jobs:offre_list')
        elif demo_role == 'tuteur':
            tut_user = Utilisateur.objects.filter(role='Tuteur').first()
            if tut_user:
                login_user(request, tut_user)
                messages.success(request, f"Connexion Démo réussie : Bienvenue {tut_user.prenom} (Tuteur)")
                return redirect('training:formation_my')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        password = (request.POST.get('password') or '').strip()
        user = authenticate_user(email, password)
        if user:
            login_user(request, user)
            messages.success(request, f"Connexion réussie ! Bienvenue, {user.prenom}.")
            
            # Redirection stricte selon les droits d'accès et rôle
            if user.role == 'Admin':
                return redirect('backoffice')
            elif user.role == 'Entreprise':
                return redirect('entreprise_posts')
            elif user.role == 'Tuteur':
                return redirect('training:formation_my')
            else:
                return redirect('jobs:offre_list')
        else:
            messages.error(request, "Adresse email ou mot de passe incorrect.")
    return render(request, 'login.html')

def logout_view(request):
    logout_user(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('login')

# ── Backoffice Admin Views ──

@admin_required
def backoffice_formations(request):
    formations = Formation.objects.select_related('tuteur').all()
    inscriptions_count = Inscription.objects.count()
    form = FormationForm()
    return render(request, 'training/formation_admin.html', {
        'formations': formations,
        'stats': {
            'total': formations.count(),
            'inscriptions': inscriptions_count,
            'actives': formations.filter(is_online=True).count(),
            'taux': '94%',
        },
        'form': form,
    })

@admin_required
def backoffice_offres(request):
    offres = OffreEmploi.objects.select_related('entreprise__utilisateur').all()
    form = OffreEmploiForm()
    return render(request, 'jobs/offre_admin.html', {
        'offres': offres,
        'stats': {
            'total': offres.count(),
            'candidatures': Candidature.objects.count(),
            'vues': '3,450',
            'actives': offres.count(),
        },
        'form': form,
    })

@admin_required
def backoffice_utilisateurs(request):
    query = (request.GET.get('q') or '').strip()
    role_filter = (request.GET.get('role') or '').strip()
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
        'query': query,
        'role_filter': role_filter,
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
def backoffice_veille(request):
    from django.db.models import Avg, Count

    rapports = (
        RapportMarche.objects
        .select_related('admin__utilisateur')
        .annotate(references_count=Count('references'))
        .order_by('-date_publication', '-id_rapport_marche')
    )
    avg_salary = RapportMarche.objects.aggregate(avg=Avg('salaire_moyen_global'))['avg']
    if avg_salary is not None:
        salaire_moyen_display = f"{avg_salary:,.0f} TND".replace(',', ' ')
    else:
        salaire_moyen_display = 'N/C'

    distinct_secteurs = (
        RapportMarche.objects
        .exclude(secteur_principal__isnull=True)
        .exclude(secteur_principal__exact='')
        .values('secteur_principal')
        .distinct()
        .count()
    )

    return render(request, 'market/rapport_admin.html', {
        'rapports': rapports,
        'stats': {
            'total_rapports': rapports.count(),
            'total_references': ReferenceRapport.objects.count(),
            'salaire_moyen': salaire_moyen_display,
            'secteurs': distinct_secteurs,
        }
    })
