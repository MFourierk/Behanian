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


class UniteVente(models.Model):
    nom = models.CharField(max_length=50, verbose_name="Nom de l'unité")
    abreviation = models.CharField(max_length=10, verbose_name="Abréviation", blank=True)

    class Meta:
        verbose_name = "Unité de vente"
        verbose_name_plural = "Unités de vente"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.abreviation})" if self.abreviation else self.nom


class Client(models.Model):
    """Client de la Cave (pour bons de commande vente)"""
    TYPE_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('vip', 'VIP'),
        ('autre', 'Autre'),
    ]
    nom = models.CharField(max_length=200, verbose_name="Nom / Raison sociale")
    type_client = models.CharField(max_length=20, choices=TYPE_CHOICES, default='particulier', verbose_name="Type")
    personne_contact = models.CharField(max_length=200, blank=True, verbose_name="Personne à contacter")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    notes = models.TextField(blank=True, verbose_name="Notes")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class BoissonBar(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('sommeil', 'En sommeil'),
        ('supprime', 'Supprimé'),
    ]
    UNITE_STANDARD_CHOICES = [
        ('bouteille', 'Bouteille'),
        ('verre', 'Verre'),
        ('cl', 'Cl'),
        ('litre', 'Litre'),
        ('autre', 'Autre (personnalisé)'),
    ]
    MODE_PRIX_CHOICES = [
        ('manuel', 'Prix saisi manuellement'),
        ('marge', 'Calculé (prix achat + marge %)'),
    ]

    reference = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Référence article")
    nom = models.CharField(max_length=100, verbose_name="Désignation")
    categorie = models.ForeignKey(CategorieBar, on_delete=models.CASCADE, verbose_name="Famille / Catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='boissons/', blank=True, null=True, verbose_name="Image")

    mode_prix = models.CharField(max_length=10, choices=MODE_PRIX_CHOICES, default='manuel', verbose_name="Mode de calcul du prix")
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix d'achat (FCFA)")
    marge = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Marge (%)")
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix de vente (FCFA)")

    unite_standard = models.CharField(max_length=20, choices=UNITE_STANDARD_CHOICES, default='bouteille', verbose_name="Unité standard")
    unite_personnalisee = models.ForeignKey(UniteVente, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité personnalisée")

    quantite_stock = models.IntegerField(default=0, verbose_name="Quantité en stock")
    seuil_alerte = models.IntegerField(default=10, verbose_name="Seuil d'alerte")
    disponible = models.BooleanField(default=True, verbose_name="Disponible à la vente")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif', verbose_name="Statut")
    est_compose = models.BooleanField(default=False, verbose_name="Article composé (pack/nomenclature)")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.mode_prix == 'marge' and self.prix_achat and self.marge:
            self.prix = self.prix_achat * (1 + self.marge / 100)
        if not self.reference:
            prefix = self.nom[:3].upper() if self.nom else "ART"
            last = BoissonBar.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.reference = f"{prefix}-{new_id:04d}"
        if self.image:
            try:
                img = Image.open(self.image)
                img = img.resize((800, 450), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                buffer.seek(0)
                self.image.save(f"{self.nom.replace(' ', '_')}.jpg", ContentFile(buffer.read()), save=False)
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def unite_affichee(self):
        if self.unite_standard == 'autre' and self.unite_personnalisee:
            return str(self.unite_personnalisee)
        return self.get_unite_standard_display()

    @property
    def est_en_rupture(self):
        return self.quantite_stock == 0

    @property
    def est_stock_bas(self):
        return 0 < self.quantite_stock <= self.seuil_alerte

    class Meta:
        verbose_name = "Article (Cave)"
        verbose_name_plural = "Articles (Cave)"
        ordering = ['categorie', 'nom']

    def __str__(self):
        return f"[{self.reference}] {self.nom}" if self.reference else self.nom


class TableBar(models.Model):
    STATUT_CHOICES = [
        ('libre', 'Libre'),
        ('occupee', 'Occupée'),
        ('reservee', 'Réservée'),
    ]
    numero = models.CharField(max_length=10, unique=True, verbose_name="Numéro de table")
    capacite = models.IntegerField(default=2, verbose_name="Capacité (personnes)")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='libre', verbose_name="Statut")
    zone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Zone (Ex: Terrasse, Intérieur)")

    class Meta:
        verbose_name = "Table (Cave)"
        verbose_name_plural = "Tables (Cave)"
        ordering = ['numero']

    def __str__(self):
        return f"Table {self.numero} - {self.get_statut_display()}"


class MouvementStockBar(models.Model):
    TYPE_MOUVEMENT = [
        ('entree', 'Entrée (Achat/Réception)'),
        ('sortie', 'Sortie (Vente)'),
        ('casse', 'Casse / Perte'),
        ('inventaire', "Ajustement d'inventaire"),
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
    TYPE_CHOICES = [
        ('achat', 'Commande Fournisseur (Achat)'),
        ('vente', 'Commande Client (Vente)'),
    ]
    STATUT_ACHAT = [
        ('brouillon',    'Brouillon'),
        ('confirme',     'Confirmé'),
        ('envoye',       'Envoyé au fournisseur'),
        ('partiel',      'Reçu partiellement'),
        ('recu',         'Reçu'),
        ('annule',       'Annulé'),
    ]
    STATUT_VENTE = [
        ('brouillon',    'Brouillon'),
        ('confirme',     'Confirmé'),
        ('partiel',      'Livré partiellement'),
        ('livre',        'Livré'),
        ('facture',      'Facturé'),
        ('annule',       'Annulé'),
    ]
    # Statuts combinés pour le champ
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('confirme',  'Confirmé'),
        ('envoye',    'Envoyé'),
        ('partiel',   'Partiel'),
        ('recu',      'Reçu'),
        ('livre',     'Livré'),
        ('facture',   'Facturé'),
        ('annule',    'Annulé'),
    ]

    type_commande = models.CharField(max_length=10, choices=TYPE_CHOICES, default='achat', verbose_name="Type")
    numero = models.CharField(max_length=30, unique=True, editable=False, verbose_name="Numéro")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    # Tiers
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Client")

    # Dates
    date_commande = models.DateField(default=timezone.now, verbose_name="Date commande")
    date_livraison_prevue = models.DateField(null=True, blank=True, verbose_name="Date livraison prévue")
    date_reception_effective = models.DateField(null=True, blank=True, verbose_name="Date réception effective")

    # Méta
    notes = models.TextField(blank=True, verbose_name="Notes / Observations")
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bons_commande_bar')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last = BonCommandeBar.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            prefix = "BC-ACH" if self.type_commande == 'achat' else "BC-VTE"
            self.numero = f"{prefix}-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(l.total_ligne for l in self.lignes.all())

    @property
    def total_recu(self):
        return sum(l.quantite_recue * l.prix_unitaire for l in self.lignes.all())

    @property
    def est_en_retard(self):
        if self.date_livraison_prevue and self.statut not in ['recu', 'livre', 'facture', 'annule']:
            return timezone.now().date() > self.date_livraison_prevue
        return False

    @property
    def statut_affiche(self):
        if self.est_en_retard:
            return 'en_retard'
        return self.statut

    @property
    def tiers_nom(self):
        if self.type_commande == 'achat':
            return str(self.fournisseur) if self.fournisseur else '—'
        return str(self.client) if self.client else '—'

    class Meta:
        verbose_name = "Bon de Commande (Cave)"
        verbose_name_plural = "Bons de Commande (Cave)"
        ordering = ['-date_commande']

    def __str__(self):
        return f"{self.numero} — {self.tiers_nom}"


class LigneBonCommandeBar(models.Model):
    bon = models.ForeignKey(BonCommandeBar, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(BoissonBar, on_delete=models.PROTECT, verbose_name="Article")
    quantite_commandee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Qté commandée")
    quantite_recue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Qté reçue / livrée")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (FCFA)")
    notes_ligne = models.CharField(max_length=200, blank=True, verbose_name="Note ligne")

    @property
    def total_ligne(self):
        return self.quantite_commandee * self.prix_unitaire

    @property
    def reliquat(self):
        return max(0, self.quantite_commandee - self.quantite_recue)

    @property
    def est_solde(self):
        return self.reliquat == 0

    class Meta:
        verbose_name = "Ligne de bon de commande"
        verbose_name_plural = "Lignes de bons de commande"

    def __str__(self):
        return f"{self.article.nom} x {self.quantite_commandee}"


class BonReceptionBar(models.Model):
    """Bon de réception Cave — lié ou non à un bon de commande"""
    STATUT_CHOICES = [
        ('brouillon',  'Brouillon'),
        ('en_cours',   'En cours'),
        ('valide',     'Validé'),
        ('annule',     'Annulé'),
    ]

    numero = models.CharField(max_length=30, unique=True, editable=False, verbose_name="Numéro")
    bon_commande = models.ForeignKey(
        BonCommandeBar, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receptions',
        verbose_name="Bon de commande lié"
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Fournisseur"
    )
    numero_document_fournisseur = models.CharField(
        max_length=100, blank=True,
        verbose_name="N° document fournisseur (facture / BL)"
    )
    operateur = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='receptions_bar', verbose_name="Opérateur"
    )
    date_reception = models.DateField(default=timezone.now, verbose_name="Date de réception")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(blank=True, verbose_name="Notes / Observations")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    valide_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validations_reception_bar', verbose_name="Validé par"
    )

    def save(self, *args, **kwargs):
        if not self.numero:
            last = BonReceptionBar.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"BR-CAVE-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(l.total_ligne for l in self.lignes.all())

    @property
    def nb_articles(self):
        return self.lignes.count()

    @property
    def a_des_ecarts(self):
        return any(l.ecart != 0 for l in self.lignes.all())

    class Meta:
        verbose_name = "Bon de Réception (Cave)"
        verbose_name_plural = "Bons de Réception (Cave)"
        ordering = ['-date_reception']

    def __str__(self):
        return f"{self.numero} — {self.fournisseur or 'Sans fournisseur'}"


class LigneBonReceptionBar(models.Model):
    bon = models.ForeignKey(BonReceptionBar, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(BoissonBar, on_delete=models.PROTECT, verbose_name="Article")
    quantite_commandee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Qté commandée (référence)"
    )
    quantite_recue = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Qté reçue"
    )
    prix_unitaire = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Prix unitaire (FCFA)"
    )
    notes_ligne = models.CharField(max_length=200, blank=True)

    @property
    def total_ligne(self):
        return self.quantite_recue * self.prix_unitaire

    @property
    def ecart(self):
        """Écart entre quantité commandée et reçue"""
        return self.quantite_recue - self.quantite_commandee

    @property
    def est_conforme(self):
        return self.ecart == 0

    class Meta:
        verbose_name = "Ligne de réception (Cave)"
        verbose_name_plural = "Lignes de réception (Cave)"

    def __str__(self):
        return f"{self.article.nom} x {self.quantite_recue}"


class InventaireBar(models.Model):
    """Session d'inventaire physique de la Cave"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_cours',  'En cours'),
        ('valide',    'Validé'),
        ('annule',    'Annulé'),
    ]
    numero = models.CharField(max_length=30, unique=True, editable=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventaires_bar')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validations_inventaire_bar')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last = InventaireBar.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"INV-CAVE-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def nb_lignes(self):
        return self.lignes.count()

    @property
    def nb_ecarts(self):
        return self.lignes.filter(ecart_quantite__ne=0).count() if hasattr(self.lignes, 'filter') else sum(1 for l in self.lignes.all() if l.ecart_quantite != 0)

    @property
    def valeur_ecart_total(self):
        return sum(abs(l.valeur_ecart) for l in self.lignes.all())

    class Meta:
        verbose_name = "Inventaire (Cave)"
        verbose_name_plural = "Inventaires (Cave)"
        ordering = ['-date_creation']

    def __str__(self):
        return self.numero


class LigneInventaireBar(models.Model):
    inventaire = models.ForeignKey(InventaireBar, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(BoissonBar, on_delete=models.PROTECT)
    quantite_theorique = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Qté théorique (système)")
    quantite_comptee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Qté comptée (physique)")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix unitaire")
    notes_ligne = models.CharField(max_length=200, blank=True)

    @property
    def ecart_quantite(self):
        return self.quantite_comptee - self.quantite_theorique

    @property
    def valeur_ecart(self):
        return self.ecart_quantite * self.prix_unitaire

    @property
    def est_conforme(self):
        return self.ecart_quantite == 0

    class Meta:
        verbose_name = "Ligne d'inventaire (Cave)"
        unique_together = ['inventaire', 'article']

    def __str__(self):
        return f"{self.article.nom} — écart: {self.ecart_quantite}"


class CasseBar(models.Model):
    """Déclaration de casse / perte / produit périmé"""
    TYPE_CHOICES = [
        ('casse',    'Casse (bouteille brisée)'),
        ('perte',    'Perte / Gâchis'),
        ('perime',   'Produit périmé'),
        ('vol',      'Vol / Disparition'),
        ('offert',   'Offert / Dégustation'),
        ('autre',    'Autre'),
    ]
    STATUT_CHOICES = [
        ('declare',  'Déclaré'),
        ('valide',   'Validé'),
        ('annule',   'Annulé'),
    ]

    numero = models.CharField(max_length=30, unique=True, editable=False)
    type_casse = models.CharField(max_length=20, choices=TYPE_CHOICES, default='casse', verbose_name="Type")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='declare')
    declare_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='casses_declarees_bar')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='casses_validees_bar')
    date_casse = models.DateField(default=timezone.now, verbose_name="Date de la casse")
    description = models.TextField(blank=True, verbose_name="Description / Circonstances")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last = CasseBar.objects.order_by('id').last()
            new_id = (last.id + 1) if last else 1
            self.numero = f"CSS-CAVE-{timezone.now().year}-{new_id:04d}"
        super().save(*args, **kwargs)

    @property
    def total_valeur(self):
        return sum(l.valeur_perte for l in self.lignes.all())

    @property
    def nb_articles(self):
        return self.lignes.count()

    class Meta:
        verbose_name = "Casse / Perte (Cave)"
        verbose_name_plural = "Casses / Pertes (Cave)"
        ordering = ['-date_casse']

    def __str__(self):
        return f"{self.numero} — {self.get_type_casse_display()}"


class LigneCasseBar(models.Model):
    casse = models.ForeignKey(CasseBar, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(BoissonBar, on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité perdue")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix unitaire (FCFA)")
    notes_ligne = models.CharField(max_length=200, blank=True)

    @property
    def valeur_perte(self):
        return self.quantite * self.prix_unitaire

    class Meta:
        verbose_name = "Ligne de casse"
        verbose_name_plural = "Lignes de casse"

    def __str__(self):
        return f"{self.article.nom} x {self.quantite}"