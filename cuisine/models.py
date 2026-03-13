from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


# ==============================================================================
# FOURNISSEURS (partagé Cave + Cuisine)
# ==============================================================================

class Fournisseur(models.Model):
    TYPE_CHOICES = [
        ('grossiste',    'Grossiste'),
        ('producteur',   'Producteur / Agriculteur'),
        ('importateur',  'Importateur'),
        ('distributeur', 'Distributeur'),
        ('autre',        'Autre'),
    ]
    nom                = models.CharField(max_length=200, verbose_name="Raison sociale")
    type_fournisseur   = models.CharField(max_length=20, choices=TYPE_CHOICES, default='grossiste', verbose_name="Type")
    personne_contact   = models.CharField(max_length=200, blank=True, verbose_name="Contact")
    telephone          = models.CharField(max_length=20,  blank=True, verbose_name="Téléphone")
    telephone2         = models.CharField(max_length=20,  blank=True, verbose_name="Téléphone 2")
    email              = models.EmailField(blank=True,    verbose_name="E-mail")
    adresse            = models.TextField(blank=True,     verbose_name="Adresse")
    ville              = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    notes              = models.TextField(blank=True,     verbose_name="Notes internes")
    actif              = models.BooleanField(default=True, verbose_name="Actif")
    date_creation      = models.DateTimeField(auto_now_add=True, null=True)
    date_modification  = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name         = "Fournisseur"
        verbose_name_plural  = "Fournisseurs"
        ordering             = ['nom']

    def __str__(self):
        return self.nom


# ==============================================================================
# INGRÉDIENTS / STOCK CUISINE
# ==============================================================================

class CategorieIngredient(models.Model):
    nom    = models.CharField(max_length=100, verbose_name="Nom")
    ordre  = models.IntegerField(default=0,   verbose_name="Ordre d'affichage")
    icone  = models.CharField(max_length=50,  blank=True, verbose_name="Icône FontAwesome", default="fa-box")

    class Meta:
        verbose_name        = "Catégorie d'ingrédient"
        verbose_name_plural = "Catégories d'ingrédients"
        ordering            = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class UniteIngredient(models.Model):
    """Unités de mesure : kg, g, L, cl, pièce, boîte, etc."""
    nom          = models.CharField(max_length=50,  verbose_name="Nom de l'unité")
    abreviation  = models.CharField(max_length=10,  verbose_name="Abréviation", blank=True)
    type_unite   = models.CharField(max_length=20,  choices=[
        ('masse',   'Masse (kg, g...)'),
        ('volume',  'Volume (L, cl, ml...)'),
        ('piece',   'Pièce / unité'),
        ('autre',   'Autre'),
    ], default='piece', verbose_name="Type d'unité")

    class Meta:
        verbose_name        = "Unité de mesure"
        verbose_name_plural = "Unités de mesure"
        ordering            = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.abreviation})" if self.abreviation else self.nom


class Ingredient(models.Model):
    STATUT_CHOICES = [
        ('actif',    'Actif'),
        ('sommeil',  'En sommeil'),
        ('supprime', 'Supprimé'),
    ]

    # Identification
    reference         = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Référence")
    nom               = models.CharField(max_length=200, verbose_name="Désignation")
    categorie         = models.ForeignKey(CategorieIngredient, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Catégorie")
    description       = models.TextField(blank=True, verbose_name="Description")

    # Unités
    unite_stock       = models.ForeignKey(UniteIngredient, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='ingredients_stock', verbose_name="Unité de stock")
    unite_recette     = models.ForeignKey(UniteIngredient, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='ingredients_recette', verbose_name="Unité recette (fiches techniques)")
    # Exemple : acheté en kg (stock), utilisé en g (recette)
    facteur_conversion = models.DecimalField(max_digits=12, decimal_places=6, default=1,
                                              verbose_name="Facteur conversion stock→recette",
                                              help_text="Ex : 1 kg = 1000 g → saisir 1000")

    # Prix & CMUP
    prix_achat        = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix d'achat unitaire (FCFA)")
    cmup              = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="CMUP (FCFA)")

    # Stock
    quantite_stock    = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name="Quantité en stock")
    seuil_alerte      = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name="Seuil d'alerte")
    stock_max         = models.DecimalField(max_digits=12, decimal_places=3, default=0, blank=True, verbose_name="Stock maximum")

    # Fournisseur privilégié
    fournisseur_principal = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
                                               verbose_name="Fournisseur principal")

    # Statut
    statut            = models.BooleanField(default=True, verbose_name="Actif")
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Ingrédient"
        verbose_name_plural = "Ingrédients"
        ordering            = ['categorie__ordre', 'nom']

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix  = self.nom[:3].upper() if self.nom else "ING"
            last    = Ingredient.objects.order_by('id').last()
            new_id  = (last.id + 1) if last else 1
            self.reference = f"ING-{prefix}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def est_en_rupture(self):
        return self.quantite_stock <= 0

    @property
    def est_stock_bas(self):
        return 0 < self.quantite_stock <= self.seuil_alerte

    @property
    def valeur_stock(self):
        return self.quantite_stock * self.cmup

    @property
    def prix_unitaire_recette(self):
        """Coût par unité recette (ex: coût par gramme)"""
        if self.facteur_conversion and self.facteur_conversion > 0:
            return self.cmup / self.facteur_conversion
        return self.cmup

    def __str__(self):
        return f"[{self.reference}] {self.nom}" if self.reference else self.nom


class MouvementStockCuisine(models.Model):
    TYPE_MOUVEMENT = [
        ('entree',     'Entrée (Réception)'),
        ('sortie',     'Sortie (Consommation)'),
        ('casse',      'Casse / Perte'),
        ('inventaire', "Ajustement d'inventaire"),
        ('production', 'Consommation production'),
    ]
    ingredient      = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement  = models.CharField(max_length=20, choices=TYPE_MOUVEMENT)
    quantite        = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Quantité")
    prix_unitaire   = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Prix unitaire")
    commentaire     = models.TextField(blank=True, null=True)
    date            = models.DateTimeField(auto_now_add=True)
    utilisateur     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            ing = self.ingredient
            if self.type_mouvement in ['entree', 'inventaire']:
                ing.quantite_stock += self.quantite
            else:
                ing.quantite_stock -= self.quantite
            ing.save()

    class Meta:
        verbose_name        = "Mouvement de stock (Cuisine)"
        verbose_name_plural = "Mouvements de stock (Cuisine)"
        ordering            = ['-date']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.ingredient.nom} x {self.quantite}"


# ==============================================================================
# BONS DE COMMANDE CUISINE
# ==============================================================================

class BonCommandeCuisine(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('confirme',  'Confirmé'),
        ('envoye',    'Envoyé au fournisseur'),
        ('partiel',   'Reçu partiellement'),
        ('recu',      'Reçu'),
        ('annule',    'Annulé'),
    ]

    numero                  = models.CharField(max_length=30, unique=True, editable=False, verbose_name="Numéro")
    fournisseur             = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur")
    statut                  = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_commande           = models.DateField(default=timezone.now, verbose_name="Date commande")
    date_livraison_prevue   = models.DateField(null=True, blank=True, verbose_name="Date livraison prévue")
    date_reception_effective = models.DateField(null=True, blank=True, verbose_name="Date réception effective")
    notes                   = models.TextField(blank=True, verbose_name="Notes")
    cree_par                = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bc_cuisine')
    date_creation           = models.DateTimeField(auto_now_add=True, null=True)
    date_modification       = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last   = BonCommandeCuisine.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"BC-CUI-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(l.total_ligne for l in self.lignes.all())

    @property
    def est_en_retard(self):
        if self.date_livraison_prevue and self.statut not in ['recu', 'annule']:
            return timezone.now().date() > self.date_livraison_prevue
        return False

    class Meta:
        verbose_name        = "Bon de Commande (Cuisine)"
        verbose_name_plural = "Bons de Commande (Cuisine)"
        ordering            = ['-date_commande']

    def __str__(self):
        return f"{self.numero} — {self.fournisseur or '—'}"


class LigneBonCommandeCuisine(models.Model):
    bon                 = models.ForeignKey(BonCommandeCuisine, on_delete=models.CASCADE, related_name='lignes')
    ingredient          = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ingrédient")
    quantite_commandee  = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Qté commandée")
    quantite_recue      = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name="Qté reçue")
    prix_unitaire       = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (FCFA)")
    notes_ligne         = models.CharField(max_length=200, blank=True, verbose_name="Note")

    @property
    def total_ligne(self):
        return self.quantite_commandee * self.prix_unitaire

    @property
    def reliquat(self):
        return max(Decimal('0'), self.quantite_commandee - self.quantite_recue)

    class Meta:
        verbose_name        = "Ligne de BC (Cuisine)"
        verbose_name_plural = "Lignes de BC (Cuisine)"

    def __str__(self):
        return f"{self.ingredient.nom} x {self.quantite_commandee}"


# ==============================================================================
# BONS DE RÉCEPTION CUISINE
# ==============================================================================

class BonReceptionCuisine(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide',    'Validé'),
        ('annule',    'Annulé'),
    ]

    numero          = models.CharField(max_length=30, unique=True, editable=False, verbose_name="Numéro")
    bon_commande    = models.ForeignKey(BonCommandeCuisine, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name="Bon de commande lié")
    fournisseur     = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name="Fournisseur")
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_reception  = models.DateField(default=timezone.now, verbose_name="Date de réception")
    notes           = models.TextField(blank=True, verbose_name="Observations / Écarts")
    valide_par      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='receptions_cuisine_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    cree_par        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='receptions_cuisine')
    date_creation   = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last   = BonReceptionCuisine.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"BR-CUI-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    def valider(self, user):
        """Valide la réception : MAJ stock + CMUP de chaque ingrédient"""
        if self.statut != 'brouillon':
            return False
        for ligne in self.lignes.all():
            ing = ligne.ingredient
            qte_recue   = ligne.quantite_recue
            prix_achat  = ligne.prix_unitaire
            # Calcul CMUP
            stock_actuel = ing.quantite_stock
            cmup_actuel  = ing.cmup
            nouveau_stock = stock_actuel + qte_recue
            if nouveau_stock > 0:
                ing.cmup = ((stock_actuel * cmup_actuel) + (qte_recue * prix_achat)) / nouveau_stock
            ing.prix_achat = prix_achat
            ing.save()
            # Mouvement de stock
            MouvementStockCuisine.objects.create(
                ingredient     = ing,
                type_mouvement = 'entree',
                quantite       = qte_recue,
                prix_unitaire  = prix_achat,
                commentaire    = f"Réception {self.numero}",
                utilisateur    = user,
            )
        self.statut          = 'valide'
        self.valide_par      = user
        self.date_validation = timezone.now()
        self.save()
        return True

    @property
    def total(self):
        return sum(l.total_ligne for l in self.lignes.all())

    class Meta:
        verbose_name        = "Bon de Réception (Cuisine)"
        verbose_name_plural = "Bons de Réception (Cuisine)"
        ordering            = ['-date_reception']

    def __str__(self):
        return self.numero


class LigneBonReceptionCuisine(models.Model):
    bon             = models.ForeignKey(BonReceptionCuisine, on_delete=models.CASCADE, related_name='lignes')
    ingredient      = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ingrédient")
    quantite_recue  = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Qté reçue")
    prix_unitaire   = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (FCFA)")
    notes_ligne     = models.CharField(max_length=200, blank=True, verbose_name="Note")

    @property
    def total_ligne(self):
        return self.quantite_recue * self.prix_unitaire

    class Meta:
        verbose_name        = "Ligne de BR (Cuisine)"
        verbose_name_plural = "Lignes de BR (Cuisine)"


# ==============================================================================
# FICHES TECHNIQUES (RECETTES)
# ==============================================================================

class CategoriePlat(models.Model):
    nom    = models.CharField(max_length=100, verbose_name="Nom")
    ordre  = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    icone  = models.CharField(max_length=50, blank=True, default="fa-utensils", verbose_name="Icône")

    class Meta:
        verbose_name        = "Catégorie de plat"
        verbose_name_plural = "Catégories de plats"
        ordering            = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class FicheTechnique(models.Model):
    """
    Recette standardisée interne.
    Calcule automatiquement le coût de revient à partir des ingrédients.
    """
    STATUT_CHOICES = [
        ('actif',    'Active'),
        ('archive',  'Archivée'),
        ('brouillon','Brouillon'),
    ]

    nom                = models.CharField(max_length=200, verbose_name="Nom de la recette", default="")
    reference          = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Référence")
    categorie          = models.ForeignKey(CategoriePlat, on_delete=models.SET_NULL, null=True, blank=True,
                                           verbose_name="Catégorie")
    description        = models.TextField(blank=True, verbose_name="Description / Méthode")
    nb_portions        = models.DecimalField(max_digits=6, decimal_places=1, default=1,
                                             verbose_name="Nombre de portions")
    temps_preparation  = models.IntegerField(default=0, verbose_name="Temps de préparation (min)")
    temps_cuisson      = models.IntegerField(default=0, verbose_name="Temps de cuisson (min)")
    statut             = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    image              = models.ImageField(upload_to='fiches_techniques/', blank=True, null=True)
    cree_par           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fiches_techniques')
    date_creation      = models.DateTimeField(auto_now_add=True)
    date_modification  = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = self.nom[:3].upper() if self.nom else "FT"
            last   = FicheTechnique.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.reference = f"FT-{prefix}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def cout_total(self):
        """Coût total de la recette (toutes portions)"""
        return sum(l.cout_ligne for l in self.lignes.all())

    @property
    def cout_par_portion(self):
        """Coût de revient par portion"""
        if self.nb_portions and self.nb_portions > 0:
            return self.cout_total / self.nb_portions
        return Decimal('0')

    class Meta:
        verbose_name        = "Fiche Technique"
        verbose_name_plural = "Fiches Techniques"
        ordering            = ['categorie__ordre', 'nom']

    def __str__(self):
        return f"[{self.reference}] {self.nom}" if self.reference else self.nom


class LigneFicheTechnique(models.Model):
    fiche       = models.ForeignKey(FicheTechnique, on_delete=models.CASCADE, related_name='lignes')
    ingredient  = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ingrédient")
    quantite    = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Quantité (unité recette)")
    notes_ligne = models.CharField(max_length=200, blank=True, verbose_name="Note (ex: haché, émincé...)")

    @property
    def cout_ligne(self):
        """Coût de cette ligne = quantité × prix unitaire recette de l'ingrédient"""
        return self.quantite * self.ingredient.prix_unitaire_recette

    @property
    def cout_affiche(self):
        return float(self.cout_ligne)

    class Meta:
        verbose_name        = "Ligne de fiche technique"
        verbose_name_plural = "Lignes de fiches techniques"
        ordering            = ['id']

    def __str__(self):
        return f"{self.ingredient.nom} × {self.quantite}"


# ==============================================================================
# PLATS / CARTE DU RESTAURANT
# ==============================================================================

class Plat(models.Model):
    """
    Ce que le client voit et commande.
    Lié à une FicheTechnique pour le calcul de marge automatique.
    """
    STATUT_CHOICES = [
        ('disponible',   'Disponible'),
        ('indisponible', 'Indisponible (rupture)'),
        ('saisonnier',   'Saisonnier'),
        ('archive',      'Archivé'),
    ]

    nom               = models.CharField(max_length=200, verbose_name="Nom du plat")
    reference         = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Référence")
    categorie         = models.ForeignKey(CategoriePlat, on_delete=models.SET_NULL, null=True, blank=True,
                                          verbose_name="Catégorie")
    description_carte = models.TextField(blank=True, verbose_name="Description pour la carte client")
    fiche_technique   = models.OneToOneField(FicheTechnique, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='plat', verbose_name="Fiche Technique liée")
    prix_vente        = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                            verbose_name="Prix de vente (FCFA)")
    statut            = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    image             = models.ImageField(upload_to='plats/', blank=True, null=True)
    ordre_carte       = models.IntegerField(default=0, verbose_name="Ordre sur la carte")
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = self.nom[:3].upper() if self.nom else "PLT"
            last   = Plat.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.reference = f"PLT-{prefix}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def cout_revient(self):
        if self.fiche_technique:
            return self.fiche_technique.cout_par_portion
        return Decimal('0')

    @property
    def marge_brute(self):
        return self.prix_vente - self.cout_revient

    @property
    def taux_marge(self):
        if self.prix_vente > 0:
            return (self.marge_brute / self.prix_vente) * 100
        return Decimal('0')

    @property
    def coefficient_multiplicateur(self):
        if self.cout_revient > 0:
            return self.prix_vente / self.cout_revient
        return Decimal('0')

    class Meta:
        verbose_name        = "Plat"
        verbose_name_plural = "Plats"
        ordering            = ['categorie__ordre', 'ordre_carte', 'nom']

    def __str__(self):
        return f"[{self.reference}] {self.nom}" if self.reference else self.nom


# ==============================================================================
# INVENTAIRE CUISINE
# ==============================================================================

class InventaireCuisine(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'En cours'),
        ('valide',    'Validé'),
        ('annule',    'Annulé'),
    ]

    numero          = models.CharField(max_length=30, unique=True, editable=False)
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_inventaire = models.DateField(default=timezone.now, verbose_name="Date de l'inventaire")
    notes           = models.TextField(blank=True, verbose_name="Observations")
    valide_par      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='inventaires_cuisine_valides')
    date_validation = models.DateTimeField(null=True, blank=True)
    cree_par        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventaires_cuisine')
    date_creation   = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last   = InventaireCuisine.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"INV-CUI-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    def valider(self, user):
        if self.statut != 'brouillon':
            return False
        for ligne in self.lignes.all():
            ecart = ligne.quantite_physique - ligne.quantite_theorique
            if ecart != 0:
                MouvementStockCuisine.objects.create(
                    ingredient     = ligne.ingredient,
                    type_mouvement = 'inventaire',
                    quantite       = ecart,
                    commentaire    = f"Inventaire {self.numero}",
                    utilisateur    = user,
                )
            ligne.ingredient.quantite_stock = ligne.quantite_physique
            ligne.ingredient.save()
        self.statut          = 'valide'
        self.valide_par      = user
        self.date_validation = timezone.now()
        self.save()
        return True

    class Meta:
        verbose_name        = "Inventaire (Cuisine)"
        verbose_name_plural = "Inventaires (Cuisine)"
        ordering            = ['-date_inventaire']

    def __str__(self):
        return self.numero


class LigneInventaireCuisine(models.Model):
    inventaire          = models.ForeignKey(InventaireCuisine, on_delete=models.CASCADE, related_name='lignes')
    ingredient          = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ingrédient")
    quantite_theorique  = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Qté théorique (stock)")
    quantite_physique   = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name="Qté physique (comptée)")

    @property
    def ecart(self):
        return self.quantite_physique - self.quantite_theorique

    @property
    def valeur_ecart(self):
        return self.ecart * self.ingredient.cmup

    class Meta:
        verbose_name        = "Ligne d'inventaire (Cuisine)"
        verbose_name_plural = "Lignes d'inventaire (Cuisine)"


# ==============================================================================
# CASSES / PERTES CUISINE
# ==============================================================================

class CasseCuisine(models.Model):
    TYPE_CHOICES = [
        ('casse',    'Casse / Bris'),
        ('perime',   'Périmé'),
        ('perte',    'Perte / Coulage'),
        ('vol',      'Vol'),
        ('offert',   'Offert / Dégustation'),
        ('autre',    'Autre'),
    ]
    STATUT_CHOICES = [
        ('declare', 'Déclaré'),
        ('valide',  'Validé — déduit du stock'),
        ('annule',  'Annulé'),
    ]

    numero          = models.CharField(max_length=30, unique=True, editable=False)
    type_casse      = models.CharField(max_length=20, choices=TYPE_CHOICES, default='casse', verbose_name="Type")
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='declare')
    date_casse      = models.DateField(default=timezone.now, verbose_name="Date")
    description     = models.TextField(blank=True, verbose_name="Description / Circonstances")
    valide_par      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='casses_cuisine_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    cree_par        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='casses_cuisine')
    date_creation   = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last   = CasseCuisine.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"CSS-CUI-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    def valider(self, user):
        if self.statut != 'declare':
            return False
        for ligne in self.lignes.all():
            MouvementStockCuisine.objects.create(
                ingredient     = ligne.ingredient,
                type_mouvement = 'casse',
                quantite       = ligne.quantite,
                commentaire    = f"Casse {self.numero} — {self.get_type_casse_display()}",
                utilisateur    = user,
            )
        self.statut          = 'valide'
        self.valide_par      = user
        self.date_validation = timezone.now()
        self.save()
        return True

    @property
    def valeur_totale(self):
        return sum(l.valeur_ligne for l in self.lignes.all())

    class Meta:
        verbose_name        = "Déclaration de casse (Cuisine)"
        verbose_name_plural = "Déclarations de casse (Cuisine)"
        ordering            = ['-date_casse']

    def __str__(self):
        return self.numero


class LigneCasseCuisine(models.Model):
    casse       = models.ForeignKey(CasseCuisine, on_delete=models.CASCADE, related_name='lignes')
    ingredient  = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ingrédient")
    quantite    = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Quantité")
    notes_ligne = models.CharField(max_length=200, blank=True, verbose_name="Note")

    @property
    def valeur_ligne(self):
        return self.quantite * self.ingredient.cmup

    class Meta:
        verbose_name        = "Ligne de casse (Cuisine)"
        verbose_name_plural = "Lignes de casse (Cuisine)"