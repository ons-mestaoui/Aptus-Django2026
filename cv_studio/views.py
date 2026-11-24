from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.auth_helpers import admin_required, get_current_user
from accounts.models import Candidat
from .models import CV, Template, RapportIA
from .forms import CVForm, TemplateForm

# ── Front Candidate CV Studio Views ──

def template_list(request):
    """Catalogue public des modèles de CV (port fidèle de cv_templates.php)."""
    templates = Template.objects.all().order_by('-id_template')
    return render(request, 'cv_studio/template_list.html', {
        'templates': templates
    })

def cv_list(request):
    """Espace personnel du candidat listant ses CVs créés (port fidèle de cv_my.php)."""
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour accéder à votre espace CV.")
        return redirect('login')
    if user.role != 'Candidat':
        messages.info(request, "L'espace CV Studio est réservé aux candidats.")
        return redirect('jobs:offre_list')

    candidat = Candidat.objects.filter(utilisateur=user).first()
    cvs = CV.objects.filter(candidat=candidat).select_related('template').order_by('-date_mise_a_jour') if candidat else CV.objects.none()
    return render(request, 'cv_studio/cv_list.html', {
        'cvs': cvs
    })

def cv_detail(request, pk):
    cv = get_object_or_404(CV.objects.select_related('candidat__utilisateur', 'template'), pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour consulter ce CV.")
        return redirect('login')
    if user.role == 'Candidat' and cv.candidat.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez consulter que vos propres CVs.")
        return redirect('cv_studio:cv_list')
    rapports = cv.rapports_ia.all()
    return render(request, 'cv_studio/cv_detail.html', {'cv': cv, 'rapports': rapports})

def cv_print(request, pk):
    """Vue dédiée à l'impression et export propre du CV (Tâche 2.3.2)."""
    cv = get_object_or_404(CV.objects.select_related('candidat__utilisateur', 'template'), pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour exporter ce CV.")
        return redirect('login')
    if user.role == 'Candidat' and cv.candidat.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez exporter que vos propres CVs.")
        return redirect('cv_studio:cv_list')

    return render(request, 'cv_studio/cv_print.html', {
        'cv': cv,
        'template': cv.template,
    })

def cv_create(request):
    """Création d'un CV avec sélection du modèle et pré-remplissage automatique (port fidèle de cv_form.php)."""
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour créer un CV.")
        return redirect('login')
    if user.role != 'Candidat':
        messages.info(request, "La création de CV est réservée aux candidats.")
        return redirect('jobs:offre_list')
    template_id = request.GET.get('template_id')
    selected_template = None
    if template_id:
        selected_template = Template.objects.filter(pk=template_id).first()

    initial = {}
    candidat = None
    if user:
        candidat, _ = Candidat.objects.get_or_create(utilisateur=user)
        initial['candidat'] = candidat
        initial['nom_complet'] = f"{user.prenom} {user.nom or ''}".strip()
        contact_parts = [user.email]
        if user.telephone:
            contact_parts.append(user.telephone)
        initial['info_contact'] = ' | '.join(contact_parts)
        if candidat.competences:
            initial['competences'] = candidat.competences
    if selected_template:
        initial['template'] = selected_template

    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            cv = form.save(commit=False)
            if candidat and not cv.candidat_id:
                cv.candidat = candidat
            if selected_template and not cv.template_id:
                cv.template = selected_template
            cv.save()

            # Création automatique du Rapport IA initial
            RapportIA.objects.get_or_create(
                cv=cv,
                defaults={
                    'score_global': 85,
                    'points_forts': 'Structure claire, rubriques ordonnées et profil pertinent.',
                    'points_faibles': 'Pensez à quantifier vos résultats récents.',
                    'suggestions': 'Ajoutez vos mots-clés techniques clés pour maximiser le score ATS.',
                }
            )

            messages.success(request, f"CV « {cv.nom_document} » créé avec succès et rattaché au modèle {cv.template.nom if cv.template else 'Standard'} !")
            return redirect('cv_studio:cv_list')
    else:
        form = CVForm(initial=initial)

    return render(request, 'cv_studio/cv_form.html', {
        'form': form,
        'selected_template': selected_template,
        'title': f"Créer un CV ({selected_template.nom})" if selected_template else 'Créer un Curriculum Vitae'
    })

def cv_update(request, pk):
    cv = get_object_or_404(CV, pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour modifier ce CV.")
        return redirect('login')
    if user.role != 'Candidat' or cv.candidat.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez modifier que vos propres CVs.")
        return redirect('cv_studio:cv_list')

    if request.method == 'POST':
        form = CVForm(request.POST, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, "CV mis à jour avec succès en base de données !")
            return redirect('cv_studio:cv_list')
    else:
        form = CVForm(instance=cv)
    return render(request, 'cv_studio/cv_form.html', {'form': form, 'title': f'Modifier {cv.nom_document}'})

def cv_delete(request, pk):
    cv = get_object_or_404(CV, pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour supprimer ce CV.")
        return redirect('login')
    if user.role != 'Candidat' or cv.candidat.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez supprimer que vos propres CVs.")
        return redirect('cv_studio:cv_list')

    if request.method == 'POST':
        nom = cv.nom_document
        cv.delete()
        messages.success(request, f"CV « {nom} » supprimé avec succès de la base de données !")
        return redirect('cv_studio:cv_list')
    return render(request, 'cv_studio/cv_confirm_delete.html', {'cv': cv})


# ── Backoffice Templates Management (Authentic PHP Port) ──

@admin_required
def template_list_admin(request):
    query = (request.GET.get('q') or '').strip()
    templates = Template.objects.all().order_by('-id_template')
    if query:
        templates = templates.filter(nom__icontains=query) | templates.filter(description__icontains=query)
    
    total_templates = Template.objects.count()
    gratuit_count = Template.objects.filter(est_premium=False).count()
    premium_count = Template.objects.filter(est_premium=True).count()
    total_cvs = CV.objects.count()

    return render(request, 'cv_studio/cv_admin.html', {
        'templates': templates,
        'stats': {
            'total_templates': total_templates,
            'gratuit': gratuit_count,
            'premium': premium_count,
            'total_cvs': total_cvs,
        },
        'query': query
    })

@admin_required
def template_create(request):
    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        tags = request.POST.getlist('description[]') or request.POST.get('description', '')
        if isinstance(tags, list):
            description = ', '.join([(t or '').strip() for t in tags if (t or '').strip()])
        else:
            description = str(tags or '').strip()
        
        structure_html = (request.POST.get('structure_html') or '').strip()
        url_miniature = (request.POST.get('url_miniature') or '').strip()
        est_premium = request.POST.get('est_premium') in ['1', 'on', 'true', True]

        data = {
            'nom': nom,
            'description': description,
            'structure_html': structure_html,
            'url_miniature': url_miniature,
            'est_premium': est_premium
        }
        form = TemplateForm(data)
        if form.is_valid():
            tpl = form.save()
            messages.success(request, f"Template '{tpl.nom}' créé avec succès dans le catalogue.")
            return redirect('backoffice_cv_templates')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = TemplateForm()

    return render(request, 'cv_studio/template_form.html', {
        'form': form,
        'template': None,
        'action': 'add',
        'title': 'Créer un Template'
    })

@admin_required
def template_update(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        tags = request.POST.getlist('description[]') or request.POST.get('description', '')
        if isinstance(tags, list):
            description = ', '.join([(t or '').strip() for t in tags if (t or '').strip()])
        else:
            description = str(tags or '').strip()

        structure_html = (request.POST.get('structure_html') or '').strip()
        url_miniature = (request.POST.get('url_miniature') or '').strip()
        est_premium = request.POST.get('est_premium') in ['1', 'on', 'true', True]

        data = {
            'nom': nom,
            'description': description,
            'structure_html': structure_html,
            'url_miniature': url_miniature,
            'est_premium': est_premium
        }
        form = TemplateForm(data, instance=template)
        if form.is_valid():
            tpl = form.save()
            messages.success(request, f"Template '{tpl.nom}' mis à jour avec succès.")
            return redirect('backoffice_cv_templates')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = TemplateForm(instance=template)

    return render(request, 'cv_studio/template_form.html', {
        'form': form,
        'template': template,
        'action': 'edit',
        'title': f'Modifier {template.nom}'
    })

@admin_required
def template_delete(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == 'POST':
        nom = template.nom
        template.delete()
        messages.success(request, f"Template « {nom} » supprimé définitivement de la base de données avec succès !")
        return redirect('backoffice_cv_templates')
    return render(request, 'cv_studio/template_confirm_delete.html', {'template': template})
