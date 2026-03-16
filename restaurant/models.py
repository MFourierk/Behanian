from django.db import models
from django.contrib.auth.models import User

class Table(models.Model):
    """Modèle pour les tables du restaurant"""
    numero = models.CharField(max_length=10, unique=True, verbose_name="Numéro")
    capacite = models.IntegerField(verbose_name="Capacité (personnes)")
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
        return f"Table {self.numero}"


class CategorieMenu(models.Model):
    """Catégories du menu (Entrées, Plats, Desserts, Boissons)"""
    nom = models.CharField(max_length=50, verbose_name="Nom")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return self.nom


from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class PlatMenu(models.Model):
    """Plats du menu"""
    nom = models.CharField(max_length=100, verbose_name="Nom du plat")
    categorie = models.ForeignKey(CategorieMenu, on_delete=models.CASCADE, verbose_name="Catégorie")
    prix = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (FCFA)", default=0)
    image = models.ImageField(upload_to='plats/', blank=True, null=True, verbose_name="Image du plat")
    temps_preparation = models.IntegerField(verbose_name="Temps de préparation (min)")
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    is_accompagnement = models.BooleanField(default=False, verbose_name="Est un accompagnement")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            target_size = (800, 450)
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            buffer.seek(0)
            file_name = f"{self.nom.replace(' ', '_')}.jpg"
            self.image.save(file_name, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Plat"
        verbose_name_plural = "Plats"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.prix} FCFA"


class Commande(models.Model):
    """Commandes du restaurant"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_preparation', 'En préparation'),
        ('prete', 'Prête'),
        ('servie', 'Servie'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Table", null=True, blank=True)
    nom_client = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom du client")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total (FCFA)")
    
    serveur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Serveur")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Commande #{self.id} - Table {self.table.numero if self.table else 'N/A'}"


class LigneCommande(models.Model):
    """Lignes de commande (détails)"""
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes', verbose_name="Commande")
    plat = models.ForeignKey(PlatMenu, on_delete=models.CASCADE, verbose_name="Plat", null=True, blank=True)
    boisson = models.ForeignKey('bar.BoissonBar', on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_commande', verbose_name="Boisson")
    accompagnement = models.ForeignKey(PlatMenu, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_accompagnement', verbose_name="Accompagnement")
    quantite = models.IntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    nom_article = models.CharField(max_length=200, blank=True, default='', verbose_name="Nom article")

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        nom = self.nom_article or (self.plat.nom if self.plat else (self.boisson.nom if self.boisson else '?'))
        return f"{self.quantite}x {nom}"

    def get_total(self):
        return self.quantite * self.prix_unitaire

    @property
    def get_nom(self):
        if self.nom_article:
            return self.nom_article
        if self.plat:
            nom = self.plat.nom
            if self.accompagnement:
                nom += f' (+ {self.accompagnement.nom})'
            return nom
        if self.boisson:
            return self.boisson.nom
        return '?'

class Reservation(models.Model):
    """Modèle pour les réservations de tables"""
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Table")
    client_nom = models.CharField(max_length=100, verbose_name="Nom du client")
    client_telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    date_reservation = models.DateTimeField(verbose_name="Date et heure")
    nombre_personnes = models.IntegerField(verbose_name="Nombre de personnes")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    statut = models.CharField(
        max_length=20,
        choices=[
            ('confirmee', 'Confirmée'),
            ('terminee', 'Terminée'),
            ('annulee', 'Annulée'),
        ],
        default='confirmee',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['date_reservation']

    def __str__(self):
        return f"Réservation {self.client_nom} - {self.table.numero}"