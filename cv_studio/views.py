import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.auth_helpers import admin_required, get_current_user
from accounts.models import Candidat, Profil
from .models import CV, Template
from .forms import CVForm, TemplateForm, parse_info_contact


DEFAULT_CV_TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  :root { --cv-accent: #6b34a3; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', Arial, sans-serif; color: #1e293b; background: #fff; padding: 36px 40px; line-height: 1.5; font-size: 13px; }
  .cv-header { border-bottom: 3px solid var(--cv-accent); padding-bottom: 18px; margin-bottom: 20px; display: flex; align-items: center; gap: 20px; }
  .cv-photo-box { flex-shrink: 0; }
  #preview-photo { width: 82px; height: 82px; border-radius: 50%; object-fit: cover; border: 3px solid var(--cv-accent); display: none; }
  .cv-name { font-size: 26px; font-weight: 800; color: #0f172a; line-height: 1.15; }
  .cv-title { font-size: 15px; font-weight: 600; color: var(--cv-accent); margin-top: 4px; }
  .cv-contact { font-size: 12px; color: #475569; margin-top: 8px; }
  .cv-section { margin-bottom: 18px; }
  .cv-section-title { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--cv-accent); border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 8px; }
  .cv-content { white-space: pre-line; color: #334155; font-size: 13px; line-height: 1.6; }
  .skill-pill { display: inline-block; background: #f1f5f9; color: #334155; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; margin: 0 6px 6px 0; border: 1px solid #e2e8f0; font-weight: 600; }
</style>
</head>
<body>
  <div class="cv-header">
    <div class="cv-photo-box"><img id="preview-photo" src="" alt=""></div>
    <div>
      <h1 class="cv-name" id="preview-nomComplet">Nom Complet</h1>
      <div class="cv-title" id="preview-titrePoste">Titre du Poste</div>
      <div class="cv-contact" id="preview-infoContact">email@exemple.com</div>
    </div>
  </div>
  <div class="cv-section">
    <div class="cv-section-title">Résumé Professionnel</div>
    <div class="cv-content summary-text" id="preview-resume"></div>
  </div>
  <div class="cv-section">
    <div class="cv-section-title">Expérience Professionnelle</div>
    <div class="cv-content" id="preview-experience"></div>
  </div>
  <div class="cv-section">
    <div class="cv-section-title">Formation &amp; Diplômes</div>
    <div class="cv-content" id="preview-formation"></div>
  </div>
  <div class="cv-section">
    <div class="cv-section-title">Compétences</div>
    <div class="cv-content" id="preview-competences"></div>
  </div>
  <div class="cv-section">
    <div class="cv-section-title">Langues</div>
    <div class="cv-content" id="preview-langues"></div>
  </div>
</body>
</html>"""


def _build_cv_payload(cv):
    """Return a clean dict representing CV fields for template HTML injection."""
    email, phone, location = parse_info_contact(cv.info_contact)
    contact_str = ' | '.join([p for p in [email, phone, location] if p])
    competences_raw = (cv.competences or '').strip()
    competences_formatted = ' • '.join([c.strip() for c in competences_raw.split(',') if c.strip()])
    return {
        'nomComplet': cv.nom_complet or '',
        'titrePoste': cv.titre_poste or '',
        'infoContact': contact_str,
        'email': email,
        'telephone': phone,
        'localisation': location,
        'resume': cv.resume or '',
        'experience': cv.experience or '',
        'formation': cv.formation or '',
        'competences': competences_formatted,
        'competencesList': [c.strip() for c in competences_raw.split(',') if c.strip()],
        'langues': cv.langues or '',
        'urlPhoto': cv.url_photo or '',
        'couleurTheme': cv.couleur_theme or '#6b34a3',
    }


def _build_rendered_cv_srcdoc(cv):
    """Build a complete self-contained HTML preview document for a CV."""
    raw_html = (cv.template.structure_html if cv.template and cv.template.structure_html else DEFAULT_CV_TEMPLATE_HTML)
    if '<html' not in raw_html.lower():
        raw_html = (
            '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">'
            '</head><body style="margin:0;padding:0;background:#fff;">'
            f'{raw_html}</body></html>'
        )

    accent = (cv.couleur_theme or '#6b34a3').strip()
    override_css = (
        '<style>'
        'html,body{overflow:hidden!important;background:#fff!important;margin:0!important;padding:0!important;}'
        '::-webkit-scrollbar{display:none!important;}'
        f':root{{--cv-accent:{accent}!important;--primary:{accent}!important;}}'
        '#cv-preview-content,.cv-render,.cv-container,.cv-page,.ats-cv{width:100%!important;min-height:100%!important;margin:0!important;box-shadow:none!important;}'
        '.skill-pill{display:inline-block;background:#f1f5f9;color:#334155;padding:3px 10px;border-radius:6px;font-size:12px;margin:0 5px 5px 0;border:1px solid #e2e8f0;}'
        '.lang-row{display:flex;justify-content:space-between;margin-bottom:6px;border-bottom:1px dashed #e2e8f0;padding-bottom:3px;font-size:13px;}'
        '</style>'
    )
    if '</head>' in raw_html.lower():
        idx = raw_html.lower().index('</head>')
        raw_html = raw_html[:idx] + override_css + raw_html[idx:]
    else:
        raw_html = override_css + raw_html

    payload_json = json.dumps(_build_cv_payload(cv)).replace('</', '<\\/')
    injector = f"""<script>
(function(){{
  const d = {payload_json};
  const setText = (sel, val) => {{
    if (!val) return;
    document.querySelectorAll(sel).forEach(el => {{ el.innerText = val; }});
  }};
  const setHtml = (sel, val) => {{
    if (!val) return;
    document.querySelectorAll(sel).forEach(el => {{ el.innerHTML = val; }});
  }};
  const esc = (s) => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const linesToHtml = (s) => esc(s).replace(/\\n/g, '<br>');
  setText('#preview-nomComplet, [data-cv-zone="nomComplet"], .cv-name, .preview-nom, .header-info h1, .cv-header h1', d.nomComplet);
  setText('#preview-titrePoste, [data-cv-zone="titrePoste"], .cv-title, .preview-titre, .cv-role, .header-info h2, .cv-header h2', d.titrePoste);
  setHtml('#preview-resume, [data-cv-zone="resume"], .summary-text, .cv-summary, .summary', linesToHtml(d.resume));
  if (d.experience) {{
    setHtml('#preview-experience, [data-cv-zone="experience"], .cv-experience, .cv-exp, .experience-list', linesToHtml(d.experience));
  }}
  if (d.formation) {{
    setHtml('#preview-formation, [data-cv-zone="formation"], .cv-formation, .cv-edu, .education-list', linesToHtml(d.formation));
  }}
  if (d.competencesList && d.competencesList.length) {{
    const pills = d.competencesList.map(s => '<span class="skill-pill">' + esc(s) + '</span>').join('');
    setHtml('#preview-competences, [data-cv-zone="competences"], .cv-competences, .cv-skills, .skills-list, .skills-grid', pills);
  }}
  if (d.langues) {{
    const langRows = d.langues.split('\\n').filter(x => x.trim()).map(line => {{
      const parts = line.split(/[—–-]/);
      const l = esc((parts[0] || '').trim());
      const lvl = esc((parts[1] || '').trim());
      return '<div class="lang-row"><strong>' + l + '</strong><span>' + lvl + '</span></div>';
    }}).join('');
    setHtml('#preview-langues, [data-cv-zone="langues"], .cv-langues, .cv-languages, .languages-list', langRows || linesToHtml(d.langues));
  }}
  if (d.infoContact) {{
    const clean = d.infoContact.split('|').map(x => esc(x.trim())).join(' • ');
    setHtml('#preview-infoContact, [data-cv-zone="contact"], .contact-info, .cv-contact, .contact-details', clean);
  }}
  if (d.urlPhoto) {{
    document.querySelectorAll('#preview-photo, .cv-photo img, .profile-img, #profile-pic, .photo-wrapper img, [data-cv-zone="photo"] img').forEach(img => {{
      img.src = d.urlPhoto;
      img.style.display = 'block';
      if (img.parentElement && img.parentElement.classList.contains('photo-wrapper')) {{
        img.parentElement.style.display = 'flex';
      }}
    }});
    document.querySelectorAll('#photo-text, .photo-text').forEach(t => {{ t.style.display = 'none'; }});
    const hp = document.querySelector('.header-photo');
    if (hp && !hp.querySelector('img')) {{
      hp.innerHTML = '<img src="' + d.urlPhoto + '" style="width:100%;height:100%;object-fit:cover;border-radius:8px;">';
    }}
  }}
}})();
</script>"""
    if '</body>' in raw_html.lower():
        idx = raw_html.lower().rindex('</body>')
        raw_html = raw_html[:idx] + injector + raw_html[idx:]
    else:
        raw_html += injector
    return raw_html


def _prepare_print_template_html(raw_html):
    """Extract head styles/links and inner body from a full HTML template so it embeds cleanly in cv_print.html."""
    if not raw_html:
        return ''
    styles = re.findall(r'<style[^>]*>[\s\S]*?</style>', raw_html, flags=re.IGNORECASE)
    links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', raw_html, flags=re.IGNORECASE)
    body_match = re.search(r'<body[^>]*>([\s\S]*?)</body>', raw_html, flags=re.IGNORECASE)
    if body_match:
        body_inner = body_match.group(1)
        # Keep only styles that were in <head> (body styles stay in body_inner)
        head_match = re.search(r'<head[^>]*>([\s\S]*?)</head>', raw_html, flags=re.IGNORECASE)
        head_styles = (
            re.findall(r'<style[^>]*>[\s\S]*?</style>', head_match.group(1), flags=re.IGNORECASE)
            if head_match else styles
        )
        combined = '\n'.join(links + head_styles) + '\n' + body_inner
    else:
        combined = raw_html

    # Scope standalone 'body {' rules inside embedded template styles to '#cv-preview-content {'
    def _scope_style(match):
        css = match.group(0)
        return re.sub(r'(?<![.\-#\w])body(?=\s*[\{,])', '#cv-preview-content', css, flags=re.IGNORECASE)

    return re.sub(r'<style[^>]*>[\s\S]*?</style>', _scope_style, combined, flags=re.IGNORECASE)


def _build_templates_map_json():
    templates = Template.objects.all().order_by('-id_template')
    tmap = {}
    for t in templates:
        tmap[str(t.id_template)] = {
            'id': t.id_template,
            'nom': t.nom,
            'html': t.structure_html or DEFAULT_CV_TEMPLATE_HTML,
        }
    tmap['default'] = {
        'id': '',
        'nom': 'Standard Aptus',
        'html': DEFAULT_CV_TEMPLATE_HTML,
    }
    return templates, json.dumps(tmap).replace('</', '<\\/')


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
    cvs = (
        CV.objects.filter(candidat=candidat).select_related('template').order_by('-date_mise_a_jour')
        if candidat else CV.objects.none()
    )

    cv_cards = []
    ready_count = 0
    last_edit = None
    today = timezone.localdate()

    for cv in cvs:
        if last_edit is None or (cv.date_mise_a_jour and cv.date_mise_a_jour > last_edit):
            last_edit = cv.date_mise_a_jour
        is_ready = bool(
            (cv.nom_complet or '').strip()
            and (cv.titre_poste or '').strip()
            and ((cv.experience or '').strip() or (cv.formation or '').strip() or (cv.competences or '').strip())
        )
        if is_ready:
            ready_count += 1
        cv_cards.append({
            'cv': cv,
            'is_ready': is_ready,
            'theme': cv.couleur_theme or '#6b34a3',
            'preview_srcdoc': _build_rendered_cv_srcdoc(cv),
        })

    if last_edit:
        local_dt = timezone.localtime(last_edit) if timezone.is_aware(last_edit) else last_edit
        formatted_last_edit = "Aujourd'hui" if local_dt.date() == today else local_dt.strftime('%d/%m/%Y')
    else:
        formatted_last_edit = '—'

    return render(request, 'cv_studio/cv_list.html', {
        'cvs': cvs,
        'cv_cards': cv_cards,
        'stats': {
            'total': len(cv_cards),
            'ready': ready_count,
            'last_edit': formatted_last_edit,
        },
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

    email, phone, location = parse_info_contact(cv.info_contact)
    skills_list = [s.strip() for s in (cv.competences or '').split(',') if s.strip()]
    languages_list = []
    for line in (cv.langues or '').splitlines():
        line = line.strip()
        if not line:
            continue
        if '-' in line or '—' in line or '–' in line:
            sep = '—' if '—' in line else ('–' if '–' in line else '-')
            parts = [p.strip() for p in line.split(sep, 1)]
            languages_list.append({'lang': parts[0], 'level': parts[1] if len(parts) > 1 else ''})
        else:
            languages_list.append({'lang': line, 'level': ''})

    return render(request, 'cv_studio/cv_detail.html', {
        'cv': cv,
        'contact': {
            'email': email,
            'telephone': phone,
            'localisation': location,
        },
        'skills_list': skills_list,
        'languages_list': languages_list,
        'preview_srcdoc': _build_rendered_cv_srcdoc(cv),
    })


def cv_print(request, pk):
    """Vue dédiée à l'impression et export propre du CV."""
    cv = get_object_or_404(CV.objects.select_related('candidat__utilisateur', 'template'), pk=pk)
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour exporter ce CV.")
        return redirect('login')
    if user.role == 'Candidat' and cv.candidat.utilisateur != user:
        messages.error(request, "Accès refusé : vous ne pouvez exporter que vos propres CVs.")
        return redirect('cv_studio:cv_list')

    email, phone, location = parse_info_contact(cv.info_contact)
    payload_json = json.dumps(_build_cv_payload(cv)).replace('</', '<\\/')
    print_template_html = (
        _prepare_print_template_html(cv.template.structure_html)
        if cv.template and cv.template.structure_html else ''
    )
    return render(request, 'cv_studio/cv_print.html', {
        'cv': cv,
        'template': cv.template,
        'print_template_html': print_template_html,
        'contact': {
            'email': email,
            'telephone': phone,
            'localisation': location,
        },
        'cv_payload_json': payload_json,
    })


def cv_create(request):
    """Création d'un CV dans le Studio 3 colonnes 6 étapes (CRUD-only)."""
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Veuillez vous connecter pour créer un CV.")
        return redirect('login')
    if user.role != 'Candidat':
        messages.info(request, "La création de CV est réservée aux candidats.")
        return redirect('jobs:offre_list')

    candidat, _ = Candidat.objects.get_or_create(utilisateur=user)
    templates, templates_map_json = _build_templates_map_json()

    template_id = request.GET.get('template_id') or request.POST.get('template')
    selected_template = Template.objects.filter(pk=template_id).first() if template_id else templates.first()

    profil = Profil.objects.filter(utilisateur=user).first()
    loc_parts = []
    if profil:
        if profil.ville:
            loc_parts.append(profil.ville)
        if profil.pays:
            loc_parts.append(profil.pays)
    default_location = ', '.join(loc_parts) if loc_parts else (profil.adresse if profil and profil.adresse else '')

    full_name = f"{user.prenom} {user.nom or ''}".strip()
    initial = {
        'nom_complet': full_name,
        'nom_document': f"CV {full_name}".strip() if full_name else '',
        'email': user.email,
        'telephone': user.telephone or '',
        'localisation': default_location,
        'competences': candidat.competences or '',
        'couleur_theme': '#6b34a3',
    }
    if selected_template:
        initial['template'] = selected_template

    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.candidat = candidat  # Enforced server-side (anti-IDOR)
            if not cv.template_id and selected_template:
                cv.template = selected_template
            cv.statut = cv.statut or 'Actif'
            cv.save()

            messages.success(
                request,
                f"CV « {cv.nom_document} » créé avec succès ({cv.template.nom if cv.template else 'Standard'}) !"
            )
            return redirect('cv_studio:cv_list')
    else:
        form = CVForm(initial=initial)

    return render(request, 'cv_studio/cv_form.html', {
        'form': form,
        'cv': None,
        'is_edit': False,
        'selected_template': selected_template,
        'templates': templates,
        'templates_map_json': templates_map_json,
        'title': f"Créer un CV ({selected_template.nom})" if selected_template else 'Créer un Curriculum Vitae',
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

    templates, templates_map_json = _build_templates_map_json()
    selected_template = cv.template or templates.first()
    if request.method == 'POST':
        post_tpl_id = request.POST.get('template')
        if post_tpl_id:
            selected_template = Template.objects.filter(pk=post_tpl_id).first() or selected_template
        form = CVForm(request.POST, instance=cv)
        if form.is_valid():
            updated_cv = form.save(commit=False)
            updated_cv.candidat = cv.candidat  # Enforced server-side (anti-IDOR)
            updated_cv.save()
            messages.success(request, "CV mis à jour avec succès en base de données !")
            return redirect('cv_studio:cv_list')
    else:
        form = CVForm(instance=cv)

    return render(request, 'cv_studio/cv_form.html', {
        'form': form,
        'cv': cv,
        'is_edit': True,
        'selected_template': selected_template,
        'templates': templates,
        'templates_map_json': templates_map_json,
        'title': f'Modifier {cv.nom_document}',
    })


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
