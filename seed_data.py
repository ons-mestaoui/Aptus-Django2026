import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptus_core.settings')
django.setup()

from accounts.models import Utilisateur, Administrateur, Candidat, Entreprise, Profil
from jobs.models import OffreEmploi, Candidature
from cv_studio.models import Template, CV, RapportIA
from training.models import Formation, Inscription
from market.models import RapportMarche, DonneeMarche
from datetime import date, datetime

print("🌱 Seeding initial demo data for Aptus Django...")

# 1. Utilisateurs & Profiles
u_admin, _ = Utilisateur.objects.get_or_create(
    email="admin@aptus.com",
    defaults={'prenom': 'Admin', 'nom': 'Aptus', 'mot_de_passe': 'admin123', 'role': 'Admin', 'telephone': '+33100000000'}
)
Administrateur.objects.get_or_create(utilisateur=u_admin, defaults={'niveau': 'SuperAdmin'})

u_ent, _ = Utilisateur.objects.get_or_create(
    email="recrutement@techcorp.com",
    defaults={'prenom': 'Sophie', 'nom': 'Martin', 'mot_de_passe': 'pass123', 'role': 'Entreprise', 'telephone': '+33145678901'}
)
ent, _ = Entreprise.objects.get_or_create(
    utilisateur=u_ent,
    defaults={'raison_sociale': 'TechCorp Solutions', 'secteur': 'Technologies de l\'information', 'siret': '12345678901234'}
)

u_cand, _ = Utilisateur.objects.get_or_create(
    email="jean.dupont@email.com",
    defaults={'prenom': 'Jean', 'nom': 'Dupont', 'mot_de_passe': 'pass123', 'role': 'Candidat', 'telephone': '+33612345678'}
)
cand, _ = Candidat.objects.get_or_create(
    utilisateur=u_cand,
    defaults={'competences': 'Python, Django, React, PostgreSQL', 'niveau_etudes': 'Master 2 Informatique', 'niveau': 'Confirmé'}
)

u_tuteur, _ = Utilisateur.objects.get_or_create(
    email="tuteur.marc@email.com",
    defaults={'prenom': 'Marc', 'nom': 'Lemoine', 'mot_de_passe': 'pass123', 'role': 'Tuteur', 'telephone': '+33698765432'}
)

# 2. Offre d'emploi & Candidature
offre1, _ = OffreEmploi.objects.get_or_create(
    titre="Développeur Fullstack Python / Django & React",
    entreprise=ent,
    defaults={
        'description': "Nous recherchons un développeur Fullstack talentueux pour rejoindre notre équipe agile. Vous participerez à la conception et à la maintenance d'applications web scalables.",
        'competences_requises': "Python 3, Django, REST Framework, JavaScript / React, Docker",
        'salaire': 48000.0,
        'date_expir': date(2027, 12, 31),
        'domaine': "Développement Web",
        'experience_requise': "2 à 4 ans",
        'question': "Parlez-nous d'un projet Django complexe que vous avez mené à bien."
    }
)

offre2, _ = OffreEmploi.objects.get_or_create(
    titre="Data Scientist / Ingénieur IA",
    entreprise=ent,
    defaults={
        'description': "TechCorp recrute un Data Scientist pour développer des algorithmes prédictifs et intégrer des LLMs dans nos flux métiers.",
        'competences_requises': "Python, Scikit-Learn, PyTorch, SQL, MLOps",
        'salaire': 55000.0,
        'date_expir': date(2027, 11, 30),
        'domaine': "Data Science & IA",
        'experience_requise': "3 ans+",
        'question': "Quelle est votre approche pour optimiser un modèle de Machine Learning en production ?"
    }
)

Candidature.objects.get_or_create(
    candidat=cand,
    offre=offre1,
    defaults={
        'reponses_ques': "J'ai développé plusieurs plateformes SaaS en Django avec API REST et intégration CI/CD.",
        'note': 16.5,
        'statut': 'en_attente'
    }
)

# 3. CV Studio & Templates
tpl, _ = Template.objects.get_or_create(
    nom="Modern Professional ATS",
    defaults={
        'description': "Template moderne, épuré et optimisé pour les robots de parsing ATS.",
        'est_premium': False
    }
)

cv1, _ = CV.objects.get_or_create(
    nom_document="CV Développeur Python Django",
    candidat=cand,
    defaults={
        'nom_complet': "Jean Dupont",
        'titre_poste': "Développeur Fullstack Python / Django",
        'resume': "Développeur passionné avec 3 ans d'expérience dans l'architecture backend Django et les applications web modernes.",
        'info_contact': "jean.dupont@email.com | +33 6 12 34 56 78 | Paris, France",
        'experience': "- Développeur Backend chez WebStudio (2 ans)\n- Stage ingénieur chez InnoTech (6 mois)",
        'formation': "Diplôme d'Ingénieur en Informatique - ESPRIT (2024)",
        'competences': "Python, Django, React, SQL, Git, Docker, Linux",
        'langues': "Français (Natif), Anglais (Courant C1)",
        'statut': "Actif",
        'template': tpl
    }
)

# 4. Formation & Inscription
form1, _ = Formation.objects.get_or_create(
    titre="Masterclass Architecture Django & API REST",
    defaults={
        'description': "Formation intensive de 3 semaines pour maîtriser Django, l'optimisation ORM, la sécurité CSRF/JWT et le déploiement.",
        'domaine': "Développement Web",
        'niveau': "Intermédiaire",
        'tuteur': u_tuteur,
        'is_online': True,
        'lien_api_room': "https://meet.google.com/aptus-django-class"
    }
)

Inscription.objects.get_or_create(
    candidat=cand,
    formation=form1,
    defaults={'statut': 'En cours', 'progression': 45}
)

# 5. Market / Veille
rap, _ = RapportMarche.objects.get_or_create(
    titre="Baromètre Salarial IT & Tendances Marché 2026",
    defaults={
        'region': "National",
        'secteur_principal': "Technologies & Digital",
        'salaire_moyen_global': 51000.0,
        'salaire_min_global': 38000.0,
        'salaire_max_global': 85000.0,
        'tendance_generale': "Forte hausse (+7.4%)",
        'niveau_demande_global': 92,
        'auteur': "Observatoire des Compétences Aptus",
        'description': "Étude approfondie sur l'évolution des salaires des développeurs et data scientists, avec une demande accrue sur Python et l'IA générative."
    }
)

DonneeMarche.objects.get_or_create(
    rapport_marche=rap,
    competence="Django & Python Backend",
    defaults={
        'domaine': "Génie Logiciel",
        'salaire_min': 42000.0,
        'salaire_max': 65000.0,
        'salaire_moyen': 52000.0,
        'demande': 340
    }
)

print("✅ Demo data seeded successfully!")
