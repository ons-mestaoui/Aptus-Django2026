from django.db import models

class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('Candidat', 'Candidat'),
        ('Entreprise', 'Entreprise'),
        ('Admin', 'Administrateur'),
        ('Tuteur', 'Tuteur'),
    ]

    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(max_length=150, unique=True)
    mot_de_passe = models.CharField(max_length=255, verbose_name="Mot de passe", db_column='motDePasse')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Candidat')
    telephone = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'utilisateur'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.prenom} {self.nom or ''} ({self.role})"


class Administrateur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, primary_key=True,
        db_column='id_admin', related_name='admin_profile'
    )
    niveau = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'administrateur'
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'

    def __str__(self):
        return f"Admin: {self.utilisateur.prenom} {self.utilisateur.nom or ''}"


class Candidat(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, primary_key=True,
        db_column='id_candidat', related_name='candidat_profile'
    )
    competences = models.TextField(null=True, blank=True)
    niveau_etudes = models.CharField(max_length=100, null=True, blank=True, db_column='niveauEtudes')
    niveau = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'candidat'
        verbose_name = 'Candidat'
        verbose_name_plural = 'Candidats'

    def __str__(self):
        return f"Candidat: {self.utilisateur.prenom} {self.utilisateur.nom or ''}"


class Entreprise(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, primary_key=True,
        db_column='id_entreprise', related_name='entreprise_profile'
    )
    secteur = models.CharField(max_length=100, null=True, blank=True)
    siret = models.CharField(max_length=14, null=True, blank=True)
    raison_sociale = models.CharField(max_length=200, null=True, blank=True, db_column='raisonSociale')

    class Meta:
        db_table = 'entreprise'
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'

    def __str__(self):
        return self.raison_sociale or f"Entreprise: {self.utilisateur.prenom} {self.utilisateur.nom or ''}"


class Profil(models.Model):
    id_profil = models.AutoField(primary_key=True)
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, db_column='id_utilisateur', related_name='profil'
    )
    photo = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    pays = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True, db_column='dateNaissance')
    linkedin = models.CharField(max_length=255, null=True, blank=True)
    site_web = models.CharField(max_length=255, null=True, blank=True, db_column='siteWeb')
    date_creation = models.DateTimeField(auto_now_add=True, db_column='dateCreation')
    date_mise_a_jour = models.DateTimeField(auto_now=True, db_column='dateMiseAJour')

    class Meta:
        db_table = 'profil'
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f"Profil de {self.utilisateur}"
