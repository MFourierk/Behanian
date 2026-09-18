from django.db import models


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


class Employe(models.Model):
    """Référentiel RH — tous les employés du complexe, avec ou sans compte utilisateur."""
    nom_complet  = models.CharField(max_length=200, verbose_name='Nom complet')
    poste        = models.CharField(max_length=100, blank=True, verbose_name='Poste / Fonction')
    salaire_base = models.PositiveIntegerField(default=0, verbose_name='Salaire mensuel (FCFA)')
    actif        = models.BooleanField(default=True, verbose_name='Actif',
                     help_text="Décocher pour retirer de la liste de paiement")
    notes        = models.TextField(blank=True, verbose_name='Notes')

    class Meta:
        ordering = ['nom_complet']
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés (RH)'

    def __str__(self):
        s = self.nom_complet
        if self.poste:
            s += f' — {self.poste}'
        return s
