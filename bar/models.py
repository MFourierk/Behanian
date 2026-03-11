from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cuisine.models import Fournisseur
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class CategorieBar(models.Model):
    nom = models.CharField(max_length=50, verbose_name="Nom")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Catégorie de Boisson"
        verbose_name_plural = "Catégories de Boissons"
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return self.nom

class BoissonBar(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de la boisson")
    categorie = models.ForeignKey(CategorieBar, on_delete=models.CASCADE, verbose_name="Catégorie")
    image = models.ImageField(upload_to='boissons/', blank=True, null=True, verbose_name="Image de la boisson")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    prix = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de Vente (FCFA)")
    quantite_stock = models.IntegerField(default=0, verbose_name="Quantité en stock")
    seuil_alerte = models.IntegerField(default=10, verbose_name="Seuil d'alerte")
    disponible = models.BooleanField(default=True, verbose_name="Disponible à la vente")
    
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
        verbose_name = "Boisson (Bar)"
        verbose_name_plural = "Boissons (Bar)"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return self.nom

class MouvementStockBar(models.Model):
    TYPE_MOUVEMENT = [
        ('entree', 'Entrée (Achat/Réception)'),
        ('sortie', 'Sortie (Vente)'),
        ('casse', 'Casse / Perte'),
        ('inventaire', 'Ajustement d\'inventaire'),
    ]
    boisson = models.ForeignKey(BoissonBar, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT)
    quantite = models.IntegerField(verbose_name="Quantité")
    date = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            if self.type_mouvement in ['entree', 'inventaire']:
                self.boisson.quantite_stock += self.quantite
            else:
                self.boisson.quantite_stock -= self.quantite
            self.boisson.save()

    class Meta:
        verbose_name = "Mouvement de stock (Bar)"
        verbose_name_plural = "Mouvements de stock (Bar)"
        ordering = ['-date']

class BonCommandeBar(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé au fournisseur'),
        ('recu', 'Reçu'),
        ('annule', 'Annulé'),
    ]
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur")
    numero = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Numéro du bon")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_commande = models.DateField(default=timezone.now)
    date_reception_prevue = models.DateField(null=True, blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last_bon = BonCommandeBar.objects.order_by('id').last()
            new_id = (last_bon.id + 1) if last_bon else 1
            self.numero = f"BC-BAR-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(ligne.total for ligne in self.lignes.all()) if self.lignes.exists() else 0

    class Meta:
        verbose_name = "Bon de Commande (Bar)"
        verbose_name_plural = "Bons de Commande (Bar)"
        ordering = ['-date_commande']
