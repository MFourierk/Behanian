from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class BonReception(models.Model):
    ETAT_CHOICES = (
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    )

    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.SET_NULL, null=True, blank=True)
    numero_document = models.CharField(max_length=50, blank=True, null=True, help_text="N° de facture ou de bon de livraison")
    operateur = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bons_reception')
    date_reception = models.DateField(default=timezone.now)
    etat = models.CharField(max_length=10, choices=ETAT_CHOICES, default='en_cours')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)



    def __str__(self):
        return f"Bon de réception n°{self.id} du {self.date_reception}"

    @property
    def total_bon(self):
        return sum(ligne.total_ligne for ligne in self.lignes.all())

    class Meta:
        verbose_name = "Bon de Réception"
        verbose_name_plural = "Bons de Réception"
        ordering = ['-date_reception']

class LigneBonReception(models.Model):
    bon_reception = models.ForeignKey(BonReception, on_delete=models.CASCADE, related_name='lignes')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_achat_unitaire = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix d'achat unitaire pour cette livraison")

    def __str__(self):
        return f"{self.quantite} x {self.ingredient.nom} pour BR n°{self.bon_reception.id}"

    @property
    def total_ligne(self):
        if self.quantite is not None and self.prix_achat_unitaire is not None:
            return self.quantite * self.prix_achat_unitaire
        return 0

    class Meta:
        verbose_name = "Ligne de Bon de Réception"
        verbose_name_plural = "Lignes des Bons de Réception"
from restaurant.models import PlatMenu

class CategorieIngredient(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Catégorie d'article"
        verbose_name_plural = "Catégories d'articles"
        ordering = ['nom']

    def __str__(self):
        return self.nom

class Fournisseur(models.Model):
    nom = models.CharField(max_length=200, unique=True, verbose_name="Nom du fournisseur")
    personne_contact = models.CharField(max_length=200, blank=True, verbose_name="Personne à contacter")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    adresse = models.TextField(blank=True, verbose_name="Adresse")

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Unite(models.Model):
    nom = models.CharField(max_length=50, unique=True, verbose_name="Nom de l'unité")
    abreviation = models.CharField(max_length=10, unique=True, verbose_name="Abréviation")

    class Meta:
        verbose_name = "Unité de mesure"
        verbose_name_plural = "Unités de mesure"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.abreviation})"


class Emplacement(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de l'emplacement")

    class Meta:
        verbose_name = "Emplacement"
        verbose_name_plural = "Emplacements"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Ingredient(models.Model):
    """Représente un article de base pour la cuisine"""
    nom = models.CharField(max_length=100, verbose_name="Nom de l'article")
    code = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Code Article")
    categorie = models.ForeignKey(CategorieIngredient, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles', verbose_name="Catégorie")
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT, verbose_name="Unité de mesure")
    quantite_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Quantité en stock")
    seuil_alerte = models.DecimalField(max_digits=10, decimal_places=3, default=5, verbose_name="Stock Minimum")
    prix_moyen = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CMUP (Prix d'achat)")
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix de vente (FCFA)")
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Emplacement")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.quantite_stock} {self.unite.abreviation if self.unite else ''})"
    
    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Synchronisation du prix de vente avec le restaurant si homonyme
        if self.prix_vente > 0:
            PlatMenu.objects.filter(nom__iexact=self.nom).update(prix=self.prix_vente)


from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class FicheTechnique(models.Model):
    """Lien entre un plat du menu et ses articles"""
    plat = models.OneToOneField(PlatMenu, on_delete=models.CASCADE, related_name='fiche_technique', verbose_name="Plat associé")
    nombre_portions = models.IntegerField(default=1, verbose_name="Nombre de portions")
    instructions = models.TextField(blank=True, null=True, verbose_name="Instructions de préparation")
    image = models.ImageField(upload_to='fiches_techniques/', blank=True, null=True, verbose_name="Image du plat")
    marge_souhaitee = models.DecimalField(max_digits=5, decimal_places=2, default=70, verbose_name="Marge souhaitée (%)", help_text="Pourcentage de marge pour calculer le prix de vente suggéré.")
    temps_preparation = models.IntegerField(default=0, verbose_name="Temps de préparation (min)")
    temps_cuisson = models.IntegerField(default=0, verbose_name="Temps de cuisson (min)")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.image:
            # Ouvrir l'image en mémoire
            img = Image.open(self.image)
            
            # Redimensionner l'image
            target_size = (800, 450)
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Sauvegarder l'image redimensionnée dans un buffer mémoire
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            buffer.seek(0)
            
            # Créer un nouveau nom de fichier pour éviter les conflits
            file_name = f"{self.plat.nom.replace(' ', '_')}.jpg"
            
            # Assigner l'image redimensionnée au champ image
            self.image.save(file_name, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Fiche Technique"
        verbose_name_plural = "Fiches Techniques"

    def cout_revient_portion(self):
        if self.nombre_portions > 0:
            return self.cout_revient() / self.nombre_portions
        return 0

    @property
    def prix_de_vente_suggere(self):
        cout = self.cout_revient_portion()
        if cout > 0 and self.marge_souhaitee > 0:
            return cout * (1 + (self.marge_souhaitee / 100))
        return 0

    @property
    def marge_sur_cout_revient(self):
        if self.plat.prix > 0 and self.cout_revient_portion() > 0:
            marge = self.plat.prix - self.cout_revient_portion()
            return (marge / self.cout_revient_portion()) * 100
        return 0

    def __str__(self):
        return f"Fiche technique - {self.plat.nom}"
    
    def cout_revient(self):
        total = 0
        for ligne in self.lignes.all():
            total += ligne.cout_estime
        return total
    
    @property
    def cout_revient_negatif(self):
        return -self.cout_revient()

    @property
    def marge_valeur(self):
        if self.plat.prix > 0:
            return self.plat.prix - self.cout_revient()
        return 0

    def check_stock(self, quantite_plats=1):
        """Vérifie si le stock est suffisant pour préparer X plats"""
        manquants = []
        possible = True
        
        for ligne in self.lignes.all():
            quantite_requise = ligne.quantite * quantite_plats
            if ligne.ingredient.quantite_stock < quantite_requise:
                possible = False
                manquants.append({
                    'article': ligne.ingredient,
                    'necessaire': quantite_requise,
                    'disponible': ligne.ingredient.quantite_stock,
                    'manque': quantite_requise - ligne.ingredient.quantite_stock
                })
        return possible, manquants

    def max_portions_possibles(self):
        """Calcule le nombre maximum de portions réalisables avec le stock actuel"""
        import math
        max_p = float('inf')
        has_ingredients = False
        
        for ligne in self.lignes.all():
            has_ingredients = True
            if ligne.quantite <= 0: continue
            
            possible = float(ligne.ingredient.quantite_stock) / float(ligne.quantite)
            if possible < max_p:
                max_p = possible
                
        if not has_ingredients:
            return 999 # Si pas d'ingrédients, on suppose illimité ou géré autrement
            
        return int(max_p) if max_p != float('inf') else 0

    def deduire_stock(self, quantite_plats=1, user=None):
        """Déduit les articles du stock"""
        possible, manquants = self.check_stock(quantite_plats)
        if not possible:
            return False, manquants
        
        for ligne in self.lignes.all():
            quantite_a_deduire = ligne.quantite * quantite_plats
            MouvementStock.objects.create(
                ingredient=ligne.ingredient,
                type_mouvement='sortie',
                quantite=quantite_a_deduire,
                commentaire=f"Préparation de {quantite_plats}x {self.plat.nom}",
                utilisateur=user
            )
        return True, []

    def restaurer_stock(self, quantite_plats=1, user=None):
        """Restaure les articles au stock (Annulation commande)"""
        for ligne in self.lignes.all():
            quantite_a_restaurer = ligne.quantite * quantite_plats
            MouvementStock.objects.create(
                ingredient=ligne.ingredient,
                type_mouvement='inventaire', 
                quantite=quantite_a_restaurer,
                commentaire=f"Annulation {quantite_plats}x {self.plat.nom}",
                utilisateur=user
            )


class LigneFicheTechnique(models.Model):
    """Article et quantité pour une fiche technique"""
    fiche = models.ForeignKey(FicheTechnique, on_delete=models.CASCADE, related_name='lignes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="Article")
    quantite = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Quantité nécessaire")
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix de Vente Spécifique")
    
    class Meta:
        verbose_name = "Ligne fiche technique"
        verbose_name_plural = "Lignes fiche technique"

    def __str__(self):
        return f"{self.ingredient.nom} - {self.quantite} {self.ingredient.unite}"
    
    @property
    def cout_estime(self):
        return self.quantite * self.ingredient.prix_moyen


class MouvementStock(models.Model):
    """Historique des mouvements de stock"""
    TYPE_MOUVEMENT = [
        ('entree', 'Entrée (Achat)'),
        ('sortie', 'Sortie (Utilisation)'),
        ('perte', 'Perte / Gâchis'),
        ('prelevement', 'Prélèvement Propriétaire'),
        ('inventaire', 'Ajustement Inventaire'),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='mouvements')
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur")
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT)
    quantite = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix unitaire (si achat)")
    date = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.ingredient.nom} ({self.quantite})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            if self.type_mouvement == 'entree':
                if self.prix_unitaire and self.quantite > 0:
                    valeur_totale_actuelle = self.ingredient.quantite_stock * self.ingredient.prix_moyen
                    valeur_nouvelle = self.quantite * self.prix_unitaire
                    nouvelle_quantite = self.ingredient.quantite_stock + self.quantite
                    if nouvelle_quantite > 0:
                        self.ingredient.prix_moyen = (valeur_totale_actuelle + valeur_nouvelle) / nouvelle_quantite
                
                self.ingredient.quantite_stock += self.quantite
                
            elif self.type_mouvement in ['sortie', 'perte', 'prelevement']:
                self.ingredient.quantite_stock -= self.quantite
                
            elif self.type_mouvement == 'inventaire':
                self.ingredient.quantite_stock += self.quantite
            
            self.ingredient.save()
