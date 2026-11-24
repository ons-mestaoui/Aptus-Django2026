from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Formation, Inscription
from .forms import FormationForm, InscriptionForm
from accounts.models import Utilisateur, Candidat
from accounts.auth_helpers import get_current_user, login_user, admin_required

def formation_list(request):
    domaine = (request.GET.get('domaine') or '').strip()
    niveau = (request.GET.get('niveau') or '').strip()
    query = (request.GET.get('q') or '').strip()
    
    formations = Formation.objects.select_related('tuteur', 'prerequis').all()
    
    # Règle métier : masquage automatique 48h après la date de fin
    limit_time = timezone.now() - timezone.timedelta(hours=48)
    formations = formations.exclude(date_fin__isnull=False, date_fin__lt=limit_time)

    if domaine:
        formations = formations.filter(domaine__icontains=domaine)
    if niveau:
        formations = formations.filter(niveau__iexact=niveau)
    if query:
        formations = formations.filter(titre__icontains=query) | formations.filter(description__icontains=query)
        
    domaines = Formation.objects.values_list('domaine', flat=True).distinct()
    domaines = [d for d in domaines if d]
    
    user = get_current_user(request)
    enrolled_ids = []
    if user and user.role == 'Candidat':
        enrolled_ids = list(Inscription.objects.filter(candidat__utilisateur=user).values_list('formation_id', flat=True))
    
    return render(request, 'training/formation_list.html', {
        'formations': formations,
        'domaines': domaines,
        'selected_domaine': domaine,
        'selected_niveau': niveau,
        'query': query,
        'total_count': formations.count(),
        'enrolled_ids': enrolled_ids,
    })

def formation_sinscrire(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour vous inscrire à cette formation.")
        return redirect('login')
    
    if user.role != 'Candidat':
        messages.warning(request, "L'inscription aux formations est réservée aux candidats.")
        return redirect('training:formation_detail', pk=formation.pk)
        
    candidat, _ = Candidat.objects.get_or_create(utilisateur=user)

    # Règle Métier Préréquis (FormationController.php):
    # Si la formation exige un prérequis, vérifier que le candidat l'a validé (progression == 100)
    if getattr(formation, 'prerequis', None):
        prereq_insc = Inscription.objects.filter(candidat=candidat, formation=formation.prerequis).first()
        if not prereq_insc or prereq_insc.progression < 100:
            messages.error(request, f"Prérequis requis : vous devez d'abord valider à 100% la formation « {formation.prerequis.titre} » avant de vous inscrire.")
            return redirect('training:formation_detail', pk=formation.pk)
    
    insc, created = Inscription.objects.get_or_create(
        candidat=candidat,
        formation=formation,
        defaults={'statut': 'En attente', 'progression': 0}
    )
    if created:
        messages.success(request, f"Félicitations ! Vous êtes inscrit à la formation « {formation.titre} ». Bienvenue dans votre espace cours !")
    else:
        messages.info(request, f"Vous participez déjà à la formation « {formation.titre} ». Accès direct au cours.")
        
    return redirect('training:formation_viewer', pk=formation.pk)

def formation_desinscrire(request, pk):
    insc = get_object_or_404(Inscription, pk=pk)
    
    # Contrainte Métier 1 (InscriptionController.php line 431):
    # Bloquer si la formation a déjà commencé (date passée)
    if insc.formation.date_formation and insc.formation.date_formation <= timezone.now():
        messages.error(request, "Impossible de se désinscrire : la session de formation a déjà débuté ou est passée.")
        return redirect('training:formation_my')

    # Contrainte Métier 2 (InscriptionController.php line 441):
    # Bloquer si la formation est terminée
    if insc.statut == 'Terminée' or insc.progression >= 100:
        messages.error(request, "Impossible de se désinscrire d'un programme de formation déjà validé et terminé.")
        return redirect('training:formation_my')

    insc.delete()
    messages.success(request, "Vous vous êtes désinscrit de la formation avec succès.")
    return redirect('training:formation_my')

def formation_my(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if user.role == 'Tuteur':
        # Espace Formateur : Formations dispensées par le tuteur connecté
        formations_tuteur = Formation.objects.filter(tuteur=user).prefetch_related('inscriptions__candidat__utilisateur')
        total_students = sum(f.inscriptions.count() for f in formations_tuteur)
        return render(request, 'training/formation_my.html', {
            'is_tuteur_view': True,
            'formations_tuteur': formations_tuteur,
            'total_cours': formations_tuteur.count(),
            'total_students': total_students,
        })

    # Espace Candidat : Cours suivis par le candidat
    if user.role == 'Candidat':
        inscriptions = Inscription.objects.filter(candidat__utilisateur=user).select_related('formation__tuteur', 'candidat__utilisateur')
    else:
        inscriptions = Inscription.objects.select_related('formation__tuteur', 'candidat__utilisateur').all()

    total_cours = inscriptions.count()
    completed_cours = inscriptions.filter(progression__gte=100).count()
    en_cours_cours = inscriptions.filter(progression__gt=0, progression__lt=100).count()
    en_attente_cours = inscriptions.filter(progression=0).count()
    global_progress = int(sum(i.progression for i in inscriptions) / total_cours) if total_cours > 0 else 0

    return render(request, 'training/formation_my.html', {
        'is_tuteur_view': False,
        'inscriptions': inscriptions,
        'total_cours': total_cours,
        'completed_cours': completed_cours,
        'en_cours_cours': en_cours_cours,
        'en_attente_cours': en_attente_cours,
        'global_progress': global_progress,
        'is_candidat_view': bool(user.role == 'Candidat')
    })

def formation_viewer(request, pk):
    """Visionneuse de cours e-learning Aptus (port fidèle de formation_viewer.php)."""
    formation = get_object_or_404(Formation.objects.select_related('tuteur'), pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour accéder à ce cours.")
        return redirect('login')

    inscription = None
    if user.role == 'Candidat':
        candidat, _ = Candidat.objects.get_or_create(utilisateur=user)
        inscription = Inscription.objects.filter(candidat=candidat, formation=formation).first()
        if not inscription:
            messages.warning(request, f"Vous devez d'abord vous inscrire à la formation « {formation.titre} » pour y accéder.")
            return redirect('training:formation_detail', pk=formation.pk)
    else:
        candidat = Candidat.objects.filter(utilisateur=user).first()
        if candidat:
            inscription = Inscription.objects.filter(candidat=candidat, formation=formation).first()

    desc_lines = [line.strip() for line in (formation.description or '').split('\n') if line.strip()]
    if not desc_lines:
        desc_lines = [
            "Introduction aux concepts fondamentaux et architecture globale",
            "Mise en pratique approfondie et exercices guidés",
            "Cas d'études appliqués et analyse de performances",
            "Projet de synthèse et validation des compétences acquises"
        ]

    total_chapters = max(len(desc_lines), 3)
    current_prog = inscription.progression if inscription else 0

    if request.method == 'POST' and inscription:
        action = request.POST.get('action')
        if action == 'complete_chapter':
            chap_num = int(request.POST.get('chapter_num', 1))
            new_prog = min(100, int((chap_num / total_chapters) * 100))
            if new_prog > inscription.progression:
                inscription.progression = new_prog
                if new_prog >= 100:
                    inscription.statut = 'Terminée'
                elif inscription.statut == 'En attente':
                    inscription.statut = 'En cours'
                inscription.save()
                messages.success(request, f"Bravo ! Chapitre {chap_num} complété ({new_prog}% de progression).")
            return redirect('training:formation_viewer', pk=formation.pk)
        elif action == 'finish_course':
            inscription.progression = 100
            inscription.statut = 'Terminée'
            inscription.save()
            messages.success(request, "Félicitations ! Vous avez validé et terminé ce programme de formation avec succès !")
            return redirect('training:formation_viewer', pk=formation.pk)

    chapters = []
    for i, line in enumerate(desc_lines, start=1):
        target_pct = int((i / total_chapters) * 100)
        is_done = current_prog >= target_pct
        chapters.append({
            'num': i,
            'title': line,
            'is_done': is_done,
            'target_pct': target_pct,
            'type': 'Théorie & Pratique' if i % 2 == 1 else 'Atelier Live & Code'
        })

    return render(request, 'training/formation_viewer.html', {
        'formation': formation,
        'inscription': inscription,
        'current_progression': current_prog,
        'chapters': chapters,
        'total_chapters': total_chapters,
        'is_completed': bool(current_prog >= 100),
    })


def formation_detail(request, pk):
    formation = get_object_or_404(Formation.objects.select_related('tuteur'), pk=pk)
    inscriptions = formation.inscriptions.select_related('candidat__utilisateur').all()
    user = get_current_user(request)
    is_enrolled = False
    user_progression = 0
    if user and user.role == 'Candidat':
        insc = Inscription.objects.filter(candidat__utilisateur=user, formation=formation).first()
        if insc:
            is_enrolled = True
            user_progression = insc.progression
    return render(request, 'training/formation_detail.html', {
        'formation': formation,
        'inscriptions': inscriptions,
        'is_enrolled': is_enrolled,
        'user_progression': user_progression
    })

@admin_required
def formation_create(request):
    if request.method == 'POST':
        form = FormationForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.save()
            messages.success(request, f"Formation '{f.titre}' créée avec succès!")
            return redirect('backoffice_formations')
    else:
        form = FormationForm()
    return render(request, 'training/formation_form.html', {'form': form, 'title': 'Créer une Formation'})

@admin_required
def formation_update(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        form = FormationForm(request.POST, request.FILES, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(request, "Formation mise à jour avec succès!")
            return redirect('backoffice_formations')
    else:
        form = FormationForm(instance=formation)
    return render(request, 'training/formation_form.html', {'form': form, 'title': f'Modifier {formation.titre}', 'formation': formation})

@admin_required
def formation_delete(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        titre = formation.titre
        formation.delete()
        messages.success(request, f"Formation « {titre} » supprimée définitivement de la base de données avec succès !")
        return redirect('backoffice_formations')
    return render(request, 'training/formation_confirm_delete.html', {'formation': formation})
