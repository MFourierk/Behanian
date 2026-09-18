from django.db import models
from django.contrib.auth.models import User


class OperateurMobileMoney(models.Model):
    nom   = models.CharField(max_length=100, verbose_name="Nom de l'opérateur")
    image = models.ImageField(upload_to='mobile_money/', blank=True, null=True, verbose_name="Logo")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Opérateur Mobile Money"
        verbose_name_plural = "Opérateurs Mobile Money"

    def __str__(self):
        return self.nom


class Coordonnees(models.Model):
    nom_complexe = models.CharField(max_length=255, default="COMPLEXE HOTELIER BEHANIAN")
    adresse = models.CharField(max_length=255, default="Yopougon Beago à 2000m du Palais de justice")
    telephone1 = models.CharField(max_length=20, default="07 58 29 11 10")
    telephone2 = models.CharField(max_length=20, default="01 43 09 76 16", blank=True)
    email = models.EmailField(default="complexebehanian@gmail.com")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    slogan = models.CharField(max_length=255, default="Votre confort, notre priorité", blank=True)

    class Meta:
        verbose_name = "Coordonnées du Complexe"
        verbose_name_plural = "Coordonnées du Complexe"

    def __str__(self):
        return self.nom_complexe

    def save(self, *args, **kwargs):
        if not self.pk and Coordonnees.objects.exists():
            # Prevent creating a new instance if one already exists
            return
        super(Coordonnees, self).save(*args, **kwargs)


class SalaireConfig(models.Model):
    """Salaire mensuel configuré par utilisateur — section RH du paramétrage."""
    user         = models.OneToOneField(User, on_delete=models.CASCADE,
                     related_name='salaire_config', verbose_name='Employé')
    salaire_base = models.PositiveIntegerField(default=0, verbose_name='Salaire mensuel (FCFA)')
    actif_paie   = models.BooleanField(default=True, verbose_name='Actif en paie',
                     help_text="Décocher pour exclure de la liste de paiement coffre")

    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = 'Salaire employé'
        verbose_name_plural = 'Salaires employés (RH)'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.salaire_base:,} FCFA"
