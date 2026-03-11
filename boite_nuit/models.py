from django.db import models
from django.contrib.auth.models import User

class TableBoite(models.Model):
    """Tables de la boîte de nuit"""
    TYPE_TABLE = [
        ('standard', 'Standard'),
        ('vip', 'VIP'),
    ]
    
    numero = models.CharField(max_length=10, unique=True, verbose_name="Numéro")
    type_table = models.CharField(max_length=20, choices=TYPE_TABLE, verbose_name="Type")
    capacite = models.IntegerField(verbose_name="Capacité (personnes)")
    prix_reservation = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix réservation (FCFA)")
    statut = models.CharField(
        max_length=20,
        choices=[
            ('disponible', 'Disponible'),
            ('occupee', 'Occupée'),
            ('reservee', 'Réservée'),
        ],
        default='disponible',
        verbose_name="Statut"
    )
    
    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ['numero']
    
    def __str__(self):
        return f"Table {self.numero} - {self.get_type_table_display()}"


class Evenement(models.Model):
    """Événements organisés à la boîte de nuit"""
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_evenement = models.DateField(verbose_name="Date de l'événement")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(null=True, blank=True, verbose_name="Heure de fin")
    prix_entree = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'entrée (FCFA)")
    capacite_max = models.IntegerField(null=True, blank=True, verbose_name="Capacité maximale")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-date_evenement']
    
    def __str__(self):
        return f"{self.titre} - {self.date_evenement}"


class EntreeBoite(models.Model):
    """Entrées à la boîte de nuit"""
    nom_client = models.CharField(max_length=100, verbose_name="Nom du client")
    nombre_personnes = models.IntegerField(default=1, verbose_name="Nombre de personnes")
    prix_entree = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'entrée (FCFA)")
    evenement = models.ForeignKey(Evenement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Événement")
    
    date_entree = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Enregistré par")
    
    class Meta:
        verbose_name = "Entrée"
        verbose_name_plural = "Entrées"
        ordering = ['-date_entree']
    
    def __str__(self):
        return f"{self.nom_client} - {self.date_entree.strftime('%d/%m/%Y %H:%M')}"


class ConsommationBoite(models.Model):
    """Consommations à la boîte de nuit"""
    table = models.ForeignKey(TableBoite, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Table")
    nom_client = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom du client")
    produit = models.CharField(max_length=100, verbose_name="Produit")
    quantite = models.IntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (FCFA)")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total (FCFA)")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    serveur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Serveur")
    
    class Meta:
        verbose_name = "Consommation"
        verbose_name_plural = "Consommations"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.produit} x{self.quantite} - {self.total} FCFA"