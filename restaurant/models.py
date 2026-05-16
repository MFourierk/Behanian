from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    cuisine_plat_id = models.IntegerField(null=True, blank=True, db_index=True,
                                          help_text="ID du plat Cuisine source — synchro permanente par ID")

    @property
    def fiche_technique(self):
        """Retourne la FicheTechnique du plat cuisine associé (via cuisine_plat_id)."""
        if not self.cuisine_plat_id:
            return None
        try:
            from cuisine.models import Plat
            plat_cuisine = Plat.objects.get(pk=self.cuisine_plat_id)
            return getattr(plat_cuisine, 'fiche_technique', None)
        except Exception:
            return None

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

# ═══════════════════════════════════════════════════════════════════════════════
# FORFAITS — Combinaisons plat(s) + boisson(s) vendues ensemble
# Ex : Forfait Piscine 10 000F = séance + demi-poulet + garniture + boisson + eau
# ═══════════════════════════════════════════════════════════════════════════════

class Forfait(models.Model):
    """Forfait = ensemble de plats et/ou boissons vendus à prix fixe."""

    MODULE_CHOICES = [
        ('piscine',    'Piscine'),
        ('hotel',      'Hôtel'),
        ('restaurant', 'Restaurant'),
        ('bar',        'Bar / Cave'),
        ('espaces',    'Espaces Événementiels'),
        ('caisse',     'Caisse / Accueil'),
        ('autre',      'Autre'),
    ]

    nom           = models.CharField(max_length=200, verbose_name="Nom du forfait")
    module        = models.CharField(max_length=20, choices=MODULE_CHOICES, default='piscine',
                                     verbose_name="Module concerné")
    prix          = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix forfait (FCFA)")
    description   = models.TextField(blank=True, verbose_name="Description")
    disponible    = models.BooleanField(default=True, verbose_name="Disponible")
    image         = models.ImageField(upload_to='forfaits/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['module', 'nom']
        verbose_name = "Forfait"
        verbose_name_plural = "Forfaits"

    def __str__(self):
        return f"{self.nom} — {int(self.prix)} F ({self.get_module_display()})"


class LigneForfait(models.Model):
    """Un élément du forfait : plat cuisine OU boisson cave."""

    TYPE_CHOICES = [
        ('plat',    'Plat cuisine'),
        ('boisson', 'Boisson cave'),
        ('autre',   'Autre prestation'),
    ]

    forfait    = models.ForeignKey(Forfait, on_delete=models.CASCADE, related_name='lignes')
    type_item  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='plat')
    # Lien vers plat cuisine (optionnel)
    plat       = models.ForeignKey('cuisine.Plat', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='forfaits')
    # Lien vers boisson bar (optionnel)
    boisson    = models.ForeignKey('bar.BoissonBar', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='forfaits')
    # Pour les prestations libres (ex : "Séance piscine")
    libelle    = models.CharField(max_length=200, blank=True,
                                  verbose_name="Libellé libre (si pas plat/boisson)")
    quantite   = models.PositiveIntegerField(default=1)
    ordre      = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        ordering = ['ordre', 'id']

    def __str__(self):
        if self.plat:
            return f"{self.quantite}× {self.plat.nom}"
        if self.boisson:
            return f"{self.quantite}× {self.boisson.nom}"
        return f"{self.quantite}× {self.libelle}"

    @property
    def nom_affiche(self):
        if self.plat:    return self.plat.nom
        if self.boisson: return self.boisson.nom
        return self.libelle

    @property
    def image_url(self):
        if self.plat and self.plat.image:    return self.plat.image.url
        if self.boisson and self.boisson.image: return self.boisson.image.url
        return None


class SouscriptionForfait(models.Model):
    """Lien entre un Forfait et un client (souscription / vente de forfait)."""

    STATUT_CHOICES = [
        ('active',    'Active'),
        ('consommee', 'Consommée'),
        ('expiree',   'Expirée'),
        ('annulee',   'Annulée'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('especes',       'Espèces'),
        ('mobile_money',  'Mobile Money'),
        ('orange_money',  'Orange Money'),
        ('wave',          'Wave'),
        ('carte_bancaire','Carte bancaire'),
        ('virement',      'Virement'),
        ('cheque',        'Chèque'),
        ('autre',         'Autre'),
    ]

    forfait          = models.ForeignKey(Forfait, on_delete=models.PROTECT,
                                         related_name='souscriptions', verbose_name="Forfait")
    # Client enregistré (optionnel — peut être un client de passage)
    client           = models.ForeignKey('facturation.Client', on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='souscriptions',
                                         verbose_name="Client enregistré")
    nom_client       = models.CharField(max_length=200, blank=True,
                                        verbose_name="Nom client (saisie libre)")
    date_souscription= models.DateTimeField(default=timezone.now,
                                            verbose_name="Date de souscription")
    date_validite    = models.DateField(null=True, blank=True,
                                        verbose_name="Date de validité")
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='active',
                                        verbose_name="Statut")
    montant_paye     = models.DecimalField(max_digits=10, decimal_places=2,
                                           verbose_name="Montant encaissé (FCFA)")
    mode_paiement    = models.CharField(max_length=30, choices=MODE_PAIEMENT_CHOICES,
                                        default='especes', verbose_name="Mode de paiement")
    reference        = models.CharField(max_length=100, blank=True,
                                        verbose_name="Référence (chambre, table…)")
    notes            = models.TextField(blank=True, verbose_name="Notes internes")
    cree_par         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='souscriptions_creees',
                                         verbose_name="Créé par")
    ticket           = models.OneToOneField('facturation.Ticket', on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='souscription',
                                            verbose_name="Ticket de caisse")

    class Meta:
        ordering = ['-date_souscription']
        verbose_name = "Souscription forfait"
        verbose_name_plural = "Souscriptions forfait"

    def __str__(self):
        return f"{self.forfait.nom} — {self.client_display} ({self.get_statut_display()})"

    @property
    def client_display(self):
        if self.client:
            return str(self.client)
        return self.nom_client or "Client inconnu"

    @property
    def est_active(self):
        if self.statut != 'active':
            return False
        if self.date_validite:
            from datetime import date
            return self.date_validite >= date.today()
        return True
