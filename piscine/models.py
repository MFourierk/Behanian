from django.db import models
from django.contrib.auth.models import User


class AccesPiscine(models.Model):
    TYPE_CLIENT = [
        ('heberge', 'Hébergé'),
        ('visiteur', 'Visiteur'),
    ]

    nom_client     = models.CharField(max_length=100)
    type_client    = models.CharField(max_length=20, choices=TYPE_CLIENT)
    nb_adultes     = models.IntegerField(default=1)
    nb_enfants     = models.IntegerField(default=0)
    prix_total     = models.DecimalField(max_digits=10, decimal_places=2)
    date_entree    = models.DateTimeField(auto_now_add=True)
    date_sortie    = models.DateTimeField(null=True, blank=True)
    reservation_hotel = models.ForeignKey(
        'hotel.Reservation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acces_piscine',
        verbose_name="Réservation hôtel liée"
    )
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    @property
    def nombre_personnes(self):
        return self.nb_adultes + self.nb_enfants

    @property
    def total_consommations(self):
        return sum(c.quantite * c.prix_unitaire for c in self.consommations.all())

    @property
    def total_general(self):
        """Prix entrée + consommations"""
        return self.prix_total + self.total_consommations

    class Meta:
        verbose_name = "Accès piscine"
        ordering = ['-date_entree']

    def __str__(self):
        return f"{self.nom_client} — {self.date_entree.strftime('%d/%m/%Y')}"


class TarifPiscine(models.Model):
    TYPE = [
        ('adulte_visiteur', 'Adulte visiteur'),
        ('enfant_visiteur', 'Enfant visiteur'),
        ('adulte_heberge',  'Adulte hébergé'),
        ('enfant_heberge',  'Enfant hébergé'),
    ]
    type_tarif    = models.CharField(max_length=30, choices=TYPE, unique=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_type_tarif_display()} — {self.prix_unitaire} F"


class ConsommationPiscine(models.Model):
    acces         = models.ForeignKey(AccesPiscine, on_delete=models.CASCADE, related_name='consommations')
    produit       = models.CharField(max_length=100)
    quantite      = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.produit} x{self.quantite}"
