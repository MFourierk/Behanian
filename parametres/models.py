from django.db import models

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
