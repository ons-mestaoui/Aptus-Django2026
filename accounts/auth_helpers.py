import bcrypt
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Utilisateur

def get_current_user(request):
    """Retrieve the logged-in Utilisateur instance from session."""
    user_id = request.session.get('user_id') or request.session.get('id_utilisateur')
    if user_id:
        try:
            return Utilisateur.objects.get(id_utilisateur=user_id)
        except Utilisateur.DoesNotExist:
            return None
    return None

def login_user(request, user):
    """Set standard user identity and role in the session."""
    request.session['id_utilisateur'] = user.id_utilisateur
    request.session['user_id'] = user.id_utilisateur
    request.session['user_name'] = f"{user.prenom} {user.nom or ''}".strip()
    request.session['user_email'] = user.email
    request.session['role'] = user.role

def logout_user(request):
    """Flush session upon logout."""
    request.session.flush()

def check_user_password(raw_password, stored_password):
    """
    Vérifie la validité d'un mot de passe en clair contre:
    1. Plaintext direct (compatibilité données brutes/tests)
    2. Hasheur standard Django (PBKDF2, Argon2, SHA1...)
    3. Bcrypt natif PHP ($2y$, $2a$, $2b$) avec normalisation du préfixe $2y$ -> $2b$
    """
    if not raw_password or not stored_password:
        return False
    if stored_password == raw_password:
        return True
    try:
        if check_password(raw_password, stored_password):
            return True
    except Exception:
        pass
    if stored_password.startswith(('$2y$', '$2a$', '$2b$')):
        try:
            norm_hash = stored_password
            if norm_hash.startswith('$2y$'):
                norm_hash = '$2b$' + norm_hash[4:]
            if bcrypt.checkpw(raw_password.encode('utf-8'), norm_hash.encode('utf-8')):
                return True
        except Exception:
            pass
    return False

def authenticate_user(email, password):
    """Verify credentials supporting PBKDF2, Bcrypt PHP, and plaintext, with auto-upgrade."""
    if not email or not password:
        return None
    user = Utilisateur.objects.filter(email__iexact=email).first()
    if not user:
        return None
    if check_user_password(password, user.mot_de_passe):
        # Auto-upgrade password to standard Django PBKDF2 if not already in PBKDF2 format
        if not user.mot_de_passe.startswith('pbkdf2_'):
            user.mot_de_passe = make_password(password)
            user.save(update_fields=['mot_de_passe'])
        return user
    return None

def admin_required(view_func):
    """Enforce that only Admin users can access the view."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        role = request.session.get('role')
        if not role:
            messages.warning(request, "Veuillez vous connecter pour accéder à l'espace administration.")
            return redirect('login')
        if role != 'Admin':
            messages.error(request, "Accès refusé : espace réservé aux administrateurs.")
            return redirect('jobs:offre_list')
        return view_func(request, *args, **kwargs)
    return _wrapped

def candidat_required(view_func):
    """Enforce that user is authenticated to perform client actions."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get('user_id') or request.session.get('id_utilisateur')
        if not user_id:
            messages.warning(request, "Veuillez vous connecter pour continuer.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def auth_context(request):
    """Context processor exposing auth state to all templates."""
    role = request.session.get('role')
    user_name = request.session.get('user_name')
    user_id = request.session.get('user_id') or request.session.get('id_utilisateur')
    user_obj = None
    if user_id:
        try:
            user_obj = Utilisateur.objects.get(id_utilisateur=user_id)
        except Utilisateur.DoesNotExist:
            pass
    return {
        'current_user_id': user_id,
        'current_user_name': user_name,
        'current_role': role,
        'current_user': user_obj,
        'user_obj': user_obj,
        'is_authenticated': bool(user_id),
        'is_admin': role == 'Admin',
        'is_candidat': role == 'Candidat',
        'is_entreprise': role == 'Entreprise',
        'is_tuteur': role == 'Tuteur',
    }
