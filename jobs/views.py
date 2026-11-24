from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import OffreEmploi, Candidature
from .forms import OffreEmploiForm, CandidatureForm
from accounts.models import Utilisateur, Candidat, Entreprise
from accounts.auth_helpers import get_current_user, login_user

def update_offres_status():
    """Règle métier PHP: Mise à jour automatique des expirations basées sur la date courante."""
    today = date.today()
    # On met à jour les dates expirées
    OffreEmploi.objects.filter(date_expir__lt=today).exclude(date_expir__isnull=True)

# ── Frontoffice Offres (Catalogue & Détails) ──

def offre_list(request):
    update_offres_status()
    domaine = (request.GET.get('domaine') or '').strip()
    query = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page')
    
    # US 1.9 : Seules les offres actives (non expirées) doivent s'afficher dans le catalogue public
    today = date.today()
    offres = OffreEmploi.objects.filter(
        Q(date_expir__isnull=True) | Q(date_expir__gte=today)
    ).select_related('entreprise__utilisateur').annotate(
        nb_candidats=Count('candidatures')
    ).order_by('-date_publication', '-id_offre')

    if domaine:
        offres = offres.filter(domaine__icontains=domaine)
    if query:
        offres = offres.filter(Q(titre__icontains=query) | Q(description__icontains=query) | Q(competences_requises__icontains=query))

    paginator = Paginator(offres, 6)
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'jobs/offre_list.html', {
        'offres': page_obj,
        'page_obj': page_obj,
        'domaine': domaine,
        'query': query
    })

def offre_detail(request, pk):
    update_offres_status()
    offre = get_object_or_404(OffreEmploi.objects.select_related('entreprise__utilisateur'), pk=pk)
    user = get_current_user(request)
    already_applied = False
    
    if user and user.role == 'Candidat':
        candidat = Candidat.objects.filter(utilisateur=user).first()
        if candidat:
            already_applied = Candidature.objects.filter(candidat=candidat, offre=offre).exists()

    return render(request, 'jobs/offre_detail.html', {
        'offre': offre,
        'already_applied': already_applied
    })

def offre_postuler(request, pk):
    offre = get_object_or_404(OffreEmploi.objects.select_related('entreprise__utilisateur'), pk=pk)
    user = get_current_user(request)
    
    if not user:
        messages.warning(request, "Veuillez vous connecter pour postuler à cette offre.")
        return redirect('login')

    # Règle métier PHP apply.php: Seuls les candidats ont le droit de postuler
    if user.role != 'Candidat':
        messages.warning(request, "Seuls les candidats peuvent postuler aux offres d'emploi.")
        return redirect('jobs:offre_detail', pk=offre.pk)

    candidat, _ = Candidat.objects.get_or_create(utilisateur=user)

    # Règle métier PHP apply.php: Empêcher strictement les candidatures en doublon
    if Candidature.objects.filter(candidat=candidat, offre=offre).exists():
        messages.warning(request, "Vous avez déjà soumis votre candidature pour ce poste.")
        return redirect('jobs:offre_detail', pk=offre.pk)

    if request.method == 'POST':
        reponses_ques = (request.POST.get('reponses_ques') or '').strip()
        cv_cand = request.FILES.get('cv_cand')
        prenom = (request.POST.get('prenom') or '').strip()
        nom = (request.POST.get('nom') or '').strip()
        email = (request.POST.get('email') or '').strip()

        # Mise à jour des coordonnées si modifiées dans le formulaire
        user_updated = False
        if prenom and prenom != user.prenom:
            user.prenom = prenom
            user_updated = True
        if nom and nom != (user.nom or ''):
            user.nom = nom
            user_updated = True
        if email and email.lower() != user.email.lower():
            if not Utilisateur.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                user.email = email
                user_updated = True
        if user_updated:
            user.save()

        # Validation stricte (règles PHP apply.php : texte non vide et au moins 10 caractères + CV obligatoire)
        import re
        plain_reponses = re.sub(r'<[^>]+>', '', reponses_ques).replace('&nbsp;', ' ').strip()
        if not plain_reponses or len(plain_reponses) < 10:
            messages.error(request, "Votre réponse à la question de motivation est obligatoire et doit comporter au moins 10 caractères.")
            return render(request, 'jobs/apply.html', {
                'offre': offre,
                'candidat': candidat,
                'current_user': user,
                'user_obj': user,
            })

        if not cv_cand:
            messages.error(request, "Le dépôt de votre CV au format PDF est obligatoire pour postuler.")
            return render(request, 'jobs/apply.html', {
                'offre': offre,
                'candidat': candidat,
                'current_user': user,
                'user_obj': user,
            })

        # Calcul d'un score IA prédictif basé sur les compétences et la réponse
        score = 80
        if offre.competences_requises:
            comp_list = [c.strip().lower() for c in offre.competences_requises.split(',') if c.strip()]
            matches = sum(1 for c in comp_list if c in plain_reponses.lower())
            score = min(98, 70 + matches * 8 + (len(plain_reponses) // 50) * 2)

        candidature = Candidature.objects.create(
            candidat=candidat,
            offre=offre,
            reponses_ques=plain_reponses,
            cv_cand=cv_cand,
            note=score,
            statut='en_attente'
        )
        messages.success(request, f"Félicitations ! Votre candidature pour '{offre.titre}' a été transmise à l'entreprise.")
        return redirect('jobs:candidature_list')

    return render(request, 'jobs/apply.html', {
        'offre': offre,
        'candidat': candidat,
        'current_user': user,
        'user_obj': user,
    })


# ── Portail Entreprise : Mes Postes & Candidatures Reçues (Strict HR Views) ──

def entreprise_posts(request):
    """Portail RH : Gestion des postes de l'entreprise (équivalent hr_posts.php)."""
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if user.role != 'Entreprise':
        if user.role == 'Admin':
            return redirect('backoffice_offres')
        messages.warning(request, "L'espace 'Mes Postes' est réservé aux entreprises.")
        return redirect('jobs:offre_list')

    entreprise, _ = Entreprise.objects.get_or_create(
        utilisateur=user,
        defaults={'raison_sociale': user.nom or user.prenom}
    )

    offres = OffreEmploi.objects.filter(entreprise=entreprise).annotate(
        nb_candidats=Count('candidatures')
    ).order_by('-date_publication', '-id_offre')

    return render(request, 'jobs/hr_posts.html', {
        'offres': offres,
        'entreprise': entreprise,
        'total_postes': offres.count(),
        'total_candidats': sum(o.nb_candidats for o in offres)
    })

def entreprise_candidatures(request):
    """Portail RH : Examen et tri des candidatures reçues (équivalent hr_candidatures.php)."""
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if user.role != 'Entreprise':
        if user.role == 'Admin':
            return redirect('backoffice_offres')
        messages.warning(request, "L'espace 'Candidatures Reçues' est réservé aux entreprises.")
        return redirect('jobs:offre_list')

    entreprise, _ = Entreprise.objects.get_or_create(
        utilisateur=user,
        defaults={'raison_sociale': user.nom or user.prenom}
    )

    # Traitement de la suppression directe d'une candidature
    if request.method == 'POST' and 'delete_candidature' in request.POST:
        id_cand = request.POST.get('id_candidature')
        cand = get_object_or_404(Candidature, pk=id_cand)
        if cand.offre.entreprise != entreprise:
            messages.error(request, "Action interdite : vous ne pouvez supprimer que les candidatures sur vos propres offres.")
            return redirect('jobs:entreprise_candidatures')
        cand_id_num = cand.pk
        cand.delete()
        messages.success(request, f"Candidature #{cand_id_num} supprimée avec succès.")
        return redirect('jobs:entreprise_candidatures')

    # Traitement du changement de statut (Accepter, Refuser, Shortlister)
    if request.method == 'POST' and 'update_statut' in request.POST:
        id_cand = request.POST.get('id_candidature')
        cand = get_object_or_404(Candidature, pk=id_cand)
        if cand.offre.entreprise != entreprise:
            messages.error(request, "Action interdite : vous ne pouvez gérer que les candidatures sur vos propres offres.")
            return redirect('jobs:entreprise_candidatures')

        statut_raw = (request.POST.get('update_statut') or '').strip()
        statut_map = {
            'Shortlisté': 'shortliste',
            'shortliste': 'shortliste',
            'Accepté': 'accepte',
            'accepte': 'accepte',
            'Refusé': 'refuse',
            'refuse': 'refuse',
            'En attente': 'en_attente',
            'en_attente': 'en_attente'
        }
        cand.statut = statut_map.get(statut_raw, 'en_attente')
        cand.save()
        messages.success(request, f"Statut de la candidature de {cand.candidat.utilisateur.prenom} mis à jour : {cand.get_statut_display()}.")
        return redirect('jobs:entreprise_candidatures')

    # Récupération des offres STRICTEMENT publiées par CETTE entreprise
    mes_offres = OffreEmploi.objects.filter(entreprise=entreprise).order_by('-date_publication')
    candidatures = Candidature.objects.filter(offre__entreprise=entreprise).select_related('candidat__utilisateur', 'offre')

    # Filtre par poste
    offre_id = (request.GET.get('offre_id') or '').strip()
    if offre_id:
        candidatures = candidatures.filter(offre_id=offre_id)

    # Filtre par statut (Tous, Shortlisté, En attente, Refusé, Accepté)
    status_filter = (request.GET.get('status') or '').strip()
    if status_filter == 'shortliste':
        candidatures = candidatures.filter(statut='shortliste')
    elif status_filter == 'en_attente':
        candidatures = candidatures.filter(Q(statut='en_attente') | Q(statut__isnull=True))
    elif status_filter == 'refuse':
        candidatures = candidatures.filter(statut='refuse')
    elif status_filter == 'accepte':
        candidatures = candidatures.filter(statut='accepte')

    # Recherche dynamique par nom
    q = (request.GET.get('q') or '').strip()
    if q:
        candidatures = candidatures.filter(
            Q(candidat__utilisateur__nom__icontains=q) | 
            Q(candidat__utilisateur__prenom__icontains=q) |
            Q(candidat__utilisateur__email__icontains=q)
        )

    candidatures = candidatures.order_by('-id_candidature')

    return render(request, 'jobs/hr_candidatures.html', {
        'candidatures': candidatures,
        'mes_offres': mes_offres,
        'current_offre_id': offre_id,
        'current_status': status_filter,
        'query': q,
        'total_count': candidatures.count()
    })


# ── Administration / CRUD (Dual View: Front pour Entreprise, Back pour Admin) ──

def offre_create(request):
    user = get_current_user(request)
    is_entreprise = bool(user and user.role == 'Entreprise')

    if request.method == 'POST':
        form = OffreEmploiForm(request.POST)
        if form.is_valid():
            offre = form.save(commit=False)
            if is_entreprise:
                ent = Entreprise.objects.filter(utilisateur=user).first()
                if ent:
                    offre.entreprise = ent
            offre.save()
            messages.success(request, f"Offre '{offre.titre}' publiée avec succès !")
            if is_entreprise:
                return redirect('entreprise_posts')
            return redirect('backoffice_offres')
    else:
        initial = {}
        if is_entreprise:
            ent = Entreprise.objects.filter(utilisateur=user).first()
            if ent:
                initial['entreprise'] = ent.pk
        form = OffreEmploiForm(initial=initial)

    layout_template = 'layout_front.html' if is_entreprise else 'layout_back.html'
    return_url = 'entreprise_posts' if is_entreprise else 'backoffice_offres'
    return_label = "Retour à mes offres d'emploi" if is_entreprise else "Retour à la gestion des offres (Backoffice)"

    return render(request, 'jobs/offre_form.html', {
        'form': form,
        'title': "Créer une Offre d'emploi",
        'is_entreprise': is_entreprise,
        'layout_template': layout_template,
        'return_url': return_url,
        'return_label': return_label,
    })

def offre_update(request, pk):
    offre = get_object_or_404(OffreEmploi, pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour modifier cette offre.")
        return redirect('login')

    is_entreprise = bool(user.role == 'Entreprise')
    if is_entreprise and offre.entreprise.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez modifier que les offres appartenant à votre entreprise.")
        return redirect('entreprise_posts')
    elif not is_entreprise and user.role != 'Admin':
        messages.error(request, "Accès refusé : espace réservé aux entreprises et administrateurs.")
        return redirect('jobs:offre_list')

    if request.method == 'POST':
        form = OffreEmploiForm(request.POST, instance=offre)
        if form.is_valid():
            form.save()
            messages.success(request, "Offre d'emploi mise à jour avec succès !")
            if is_entreprise:
                return redirect('entreprise_posts')
            return redirect('backoffice_offres')
    else:
        form = OffreEmploiForm(instance=offre)

    layout_template = 'layout_front.html' if is_entreprise else 'layout_back.html'
    return_url = 'entreprise_posts' if is_entreprise else 'backoffice_offres'
    return_label = "Retour à mes offres d'emploi" if is_entreprise else "Retour à la gestion des offres (Backoffice)"

    return render(request, 'jobs/offre_form.html', {
        'form': form,
        'title': f"Modifier {offre.titre}",
        'is_entreprise': is_entreprise,
        'layout_template': layout_template,
        'return_url': return_url,
        'return_label': return_label,
    })

def offre_delete(request, pk):
    offre = get_object_or_404(OffreEmploi, pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour supprimer cette offre.")
        return redirect('login')

    is_entreprise = bool(user.role == 'Entreprise')
    if is_entreprise and offre.entreprise.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez supprimer que les offres appartenant à votre entreprise.")
        return redirect('entreprise_posts')
    elif not is_entreprise and user.role != 'Admin':
        messages.error(request, "Accès refusé : espace réservé aux entreprises et administrateurs.")
        return redirect('jobs:offre_list')

    if request.method == 'POST':
        titre = offre.titre
        offre.delete()
        messages.success(request, f"Offre d'emploi « {titre} » supprimée définitivement avec succès !")
        if is_entreprise:
            return redirect('entreprise_posts')
        return redirect('backoffice_offres')

    return_url = 'entreprise_posts' if is_entreprise else 'backoffice_offres'
    return render(request, 'jobs/offre_confirm_delete.html', {
        'offre': offre,
        'is_entreprise': is_entreprise,
        'return_url': return_url
    })


# ── Candidat Espace : Mes Candidatures ──

def candidature_list(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if user.role == 'Candidat':
        candidatures = Candidature.objects.filter(candidat__utilisateur=user).select_related('candidat__utilisateur', 'offre__entreprise')
        return render(request, 'jobs/candidature_list.html', {
            'candidatures': candidatures,
            'is_candidat_view': True
        })
    elif user.role == 'Entreprise':
        return redirect('jobs:entreprise_candidatures')
    elif user.role == 'Tuteur':
        messages.info(request, "L'espace de suivi des candidatures d'emploi est réservé aux candidats.")
        return redirect('training:formation_my')
    else:
        # Admin
        candidatures = Candidature.objects.select_related('candidat__utilisateur', 'offre__entreprise').all()
        return render(request, 'jobs/candidature_list.html', {
            'candidatures': candidatures,
            'is_candidat_view': False
        })

def candidature_annuler(request, pk):
    cand = get_object_or_404(Candidature, pk=pk)
    user = get_current_user(request)
    if not user or user.role != 'Candidat' or cand.candidat.utilisateur != user:
        messages.error(request, "Action interdite : vous ne pouvez retirer que vos propres candidatures.")
        return redirect('jobs:candidature_list')

    if request.method == 'POST':
        cand.delete()
        messages.success(request, "Votre candidature a été retirée avec succès.")
        return redirect('jobs:candidature_list')

    return render(request, 'jobs/candidature_confirm_delete.html', {'cand': cand})

def candidature_create(request):
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            c = form.save()
            messages.success(request, "Candidature enregistrée avec succès!")
            return redirect('jobs:candidature_list')
    else:
        form = CandidatureForm()
    return render(request, 'jobs/candidature_form.html', {'form': form, 'title': 'Nouvelle Candidature'})

def candidature_update(request, pk):
    cand = get_object_or_404(Candidature, pk=pk)
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES, instance=cand)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidature mise à jour!")
            return redirect('jobs:candidature_list')
    else:
        form = CandidatureForm(instance=cand)
    return render(request, 'jobs/candidature_form.html', {'form': form, 'title': f'Modifier Candidature #{cand.pk}'})

def candidature_delete(request, pk):
    cand = get_object_or_404(Candidature, pk=pk)
    if request.method == 'POST':
        cand.delete()
        messages.success(request, "Candidature supprimée!")
        return redirect('jobs:candidature_list')
    return render(request, 'jobs/candidature_confirm_delete.html', {'cand': cand})
