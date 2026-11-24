from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.auth_helpers import admin_required, get_current_user
from accounts.models import Administrateur
from .forms import RapportMarcheForm, ReferenceRapportFormSet
from .models import RapportMarche


def _get_admin_profile(request):
    """Resolve or create the Administrateur profile for the authenticated user."""
    user = get_current_user(request)
    if user:
        admin_profile, _ = Administrateur.objects.get_or_create(utilisateur=user)
        return admin_profile
    return None


def rapport_list(request):
    rapports = (
        RapportMarche.objects
        .select_related('admin__utilisateur')
        .annotate(references_count=Count('references'))
        .order_by('-date_publication', '-id_rapport_marche')
    )
    return render(request, 'market/rapport_list.html', {'rapports': rapports})


def rapport_detail(request, pk):
    rapport = get_object_or_404(RapportMarche.objects.select_related('admin__utilisateur'), pk=pk)
    references = rapport.references.all()
    return render(request, 'market/rapport_detail.html', {'rapport': rapport, 'references': references})


@admin_required
def rapport_create(request):
    if request.method == 'POST':
        form = RapportMarcheForm(request.POST)
        formset = ReferenceRapportFormSet(request.POST, prefix='references')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                rapport = form.save(commit=False)
                admin_profile = _get_admin_profile(request)
                if admin_profile:
                    rapport.admin = admin_profile
                rapport.save()
                formset.instance = rapport
                formset.save()
            messages.success(request, f"Rapport '{rapport.titre}' créé avec succès!")
            return redirect('backoffice_veille')
    else:
        form = RapportMarcheForm()
        formset = ReferenceRapportFormSet(prefix='references')
    return render(request, 'market/rapport_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Créer un Rapport de Marché',
    })


@admin_required
def rapport_update(request, pk):
    rapport = get_object_or_404(RapportMarche, pk=pk)
    if request.method == 'POST':
        form = RapportMarcheForm(request.POST, instance=rapport)
        formset = ReferenceRapportFormSet(request.POST, instance=rapport, prefix='references')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                updated = form.save(commit=False)
                if not updated.admin:
                    admin_profile = _get_admin_profile(request)
                    if admin_profile:
                        updated.admin = admin_profile
                updated.save()
                formset.save()
            messages.success(request, "Rapport mis à jour avec succès!")
            return redirect('backoffice_veille')
    else:
        form = RapportMarcheForm(instance=rapport)
        formset = ReferenceRapportFormSet(instance=rapport, prefix='references')
    return render(request, 'market/rapport_form.html', {
        'form': form,
        'formset': formset,
        'rapport': rapport,
        'title': f'Modifier {rapport.titre}',
    })


@admin_required
def rapport_delete(request, pk):
    rapport = get_object_or_404(RapportMarche, pk=pk)
    if request.method == 'POST':
        titre = rapport.titre
        rapport.delete()
        messages.success(request, f"Rapport « {titre} » supprimé définitivement de la base de données avec succès !")
        return redirect('backoffice_veille')
    return render(request, 'market/rapport_confirm_delete.html', {'rapport': rapport})
