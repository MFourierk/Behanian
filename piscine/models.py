from django.db import models
from django.contrib.auth.models import User

class AccesPiscine(models.Model):
    """Modèle pour les accès à la piscine"""
    TYPE_CLIENT = [
        ('heberge', 'Hébergé'),
        ('visiteur', 'Visiteur'),
    ]
    
    nom_client = models.CharField(max_length=100, verbose_name="Nom du client")
    type_client = models.CharField(max_length=20, choices=TYPE_CLIENT, verbose_name="Type")
    nombre_personnes = models.IntegerField(default=1, verbose_name="Nombre de personnes")
    prix_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total (FCFA)")
    
    date_entree = models.DateTimeField(auto_now_add=True, verbose_name="Date d'entrée")
    date_sortie = models.DateTimeField(null=True, blank=True, verbose_name="Date de sortie")
    
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Enregistré par")
    
    class Meta:
        verbose_name = "Accès piscine"
        verbose_name_plural = "Accès piscine"
        ordering = ['-date_entree']
    
    def __str__(self):
        return f"{self.nom_client} - {self.type_client} - {self.date_entree.strftime('%d/%m/%Y')}"


class TarifPiscine(models.Model):
    """Tarifs d'accès à la piscine"""
    TYPE_CLIENT = [
        ('heberge', 'Hébergé'),
        ('visiteur', 'Visiteur'),
    ]
    
    type_client = models.CharField(max_length=20, choices=TYPE_CLIENT, unique=True, verbose_name="Type de client")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix par personne (FCFA)")
    
    class Meta:
        verbose_name = "Tarif piscine"
        verbose_name_plural = "Tarifs piscine"
    
    def __str__(self):
        return f"{self.get_type_client_display()} - {self.prix_unitaire} FCFA"


class ConsommationPiscine(models.Model):
    """Consommations à la piscine"""
    acces = models.ForeignKey(AccesPiscine, on_delete=models.CASCADE, related_name='consommations', verbose_name="Accès")
    produit = models.CharField(max_length=100, verbose_name="Produit")
    quantite = models.IntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (FCFA)")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Consommation"
        verbose_name_plural = "Consommations"
    
    def __str__(self):
        return f"{self.produit} x{self.quantite}"
    
    def get_total(self):
        return self.quantite * self.prix_unitaire