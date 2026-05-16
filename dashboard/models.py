from django.db import models
from django.contrib.auth.models import User


class Configuration(models.Model):
    nom_complexe = models.CharField(max_length=255, default="COMPLEXE HOTELIER BEHANIAN")
    adresse = models.TextField(blank=True, default="Yopougon Beago à 2000m du Palais de justice")
    telephone = models.CharField(max_length=100, blank=True, default="07 58 29 11 10 / 01 43 09 76 16")
    email = models.EmailField(blank=True, default="complexebehanian@gmail.com")
    site_web = models.URLField(blank=True)
    notes_pied_de_page = models.TextField(blank=True, help_text="Informations légales ou autres notes à afficher en bas des documents")

    def __str__(self):
        return "Configuration Générale du Site"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(Configuration, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Empêche la suppression de l'objet de configuration unique
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "Configuration du Complexe"
        verbose_name_plural = "Configuration du Complexe"


class JournalReset(models.Model):
    """Trace immuable de chaque remise à zéro effectuée sur le système."""

    TYPE_CHOICES = [
        ('partiel',      'Remise Partielle'),
        ('complet',      'Remise Totale'),
        ('personnalise', 'Remise Personnalisée'),
    ]

    date          = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    utilisateur   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name="Exécuté par"
    )
    type_reset    = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    modules       = models.JSONField(default=dict, verbose_name="Modules supprimés")
    counts_avant  = models.JSONField(default=dict, verbose_name="Comptages avant reset")
    backup_path   = models.CharField(max_length=500, blank=True, verbose_name="Fichier backup")
    succes        = models.BooleanField(default=True, verbose_name="Succès")
    erreur        = models.TextField(blank=True, verbose_name="Message d'erreur")

    class Meta:
        verbose_name        = "Journal de remise à zéro"
        verbose_name_plural = "Journal des remises à zéro"
        ordering            = ['-date']

    def __str__(self):
        return (
            f"Reset {self.get_type_reset_display()} — "
            f"{self.date.strftime('%d/%m/%Y %H:%M')} — "
            f"{self.utilisateur or 'Système'}"
        )

    def delete(self, *args, **kwargs):
        """Le journal est en lecture seule — la suppression est bloquée."""
        pass