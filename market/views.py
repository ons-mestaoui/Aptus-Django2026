from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.auth_helpers import admin_required
from .models import RapportMarche, DonneeMarche
from .forms import RapportMarcheForm, DonneeMarcheForm

def rapport_list(request):
    rapports = RapportMarche.objects.select_related('admin__utilisateur').all()
    return render(request, 'market/rapport_list.html', {'rapports': rapports})

def rapport_detail(request, pk):
    rapport = get_object_or_404(RapportMarche.objects.select_related('admin__utilisateur'), pk=pk)
    donnees = rapport.donnees.all()
    return render(request, 'market/rapport_detail.html', {'rapport': rapport, 'donnees': donnees})

@admin_required
def rapport_create(request):
    if request.method == 'POST':
        form = RapportMarcheForm(request.POST)
        if form.is_valid():
            r = form.save()
            messages.success(request, f"Rapport '{r.titre}' créé avec succès!")
            return redirect('backoffice_veille')
    else:
        form = RapportMarcheForm()
    return render(request, 'market/rapport_form.html', {'form': form, 'title': 'Créer un Rapport de Marché'})

@admin_required
def rapport_update(request, pk):
    rapport = get_object_or_404(RapportMarche, pk=pk)
    if request.method == 'POST':
        form = RapportMarcheForm(request.POST, instance=rapport)
        if form.is_valid():
            form.save()
            messages.success(request, "Rapport mis à jour avec succès!")
            return redirect('backoffice_veille')
    else:
        form = RapportMarcheForm(instance=rapport)
    return render(request, 'market/rapport_form.html', {'form': form, 'title': f'Modifier {rapport.titre}'})

@admin_required
def rapport_delete(request, pk):
    rapport = get_object_or_404(RapportMarche, pk=pk)
    if request.method == 'POST':
        titre = rapport.titre
        rapport.delete()
        messages.success(request, f"Rapport « {titre} » supprimé définitivement de la base de données avec succès !")
        return redirect('backoffice_veille')
    return render(request, 'market/rapport_confirm_delete.html', {'rapport': rapport})
