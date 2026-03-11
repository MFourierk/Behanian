from django.db import models

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