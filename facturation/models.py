from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    nif = models.CharField(max_length=50, blank=True, verbose_name="NIF")
    stat = models.CharField(max_length=50, blank=True, verbose_name="STAT")
    
    class Meta:
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.nom} {self.prenom}".strip()
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}".strip()


class Service(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom


class Article(models.Model):
    """
    Modèle générique pour représenter un article facturable.
    Il peut pointer vers n'importe quel autre modèle via une GenericForeignKey.
    Ex: une Chambre, un Plat, un Espace de location, etc.
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='articles')
    
    # Champs pour la GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['service']
        # Assurer que chaque objet n'est référencé qu'une seule fois
        unique_together = ('content_type', 'object_id')

    def __str__(self):
        return self.nom

    @property
    def nom(self):
        """Retourne le nom de l'objet lié."""
        return getattr(self.content_object, 'nom', str(self.content_object))

    @property
    def prix_unitaire(self):
        """Retourne le prix de l'objet lié."""
        if hasattr(self.content_object, 'prix_heure'):
            return self.content_object.prix_heure # Pour EspaceLocation
        elif hasattr(self.content_object, 'prix_unitaire'):
            return self.content_object.prix_unitaire # Pour Plats, etc.
        elif hasattr(self.content_object, 'prix'):
            return self.content_object.prix # Pour Chambres, etc.
        return Decimal('0.00')


class Facture(models.Model):
    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_facturation = models.DateField(default=timezone.now)
    date_echeance = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='draft')
    
    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Champs de paiement
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date_paiement = models.DateTimeField(blank=True, null=True)
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Facture {self.numero} - {self.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        self.sous_total = sum(line.montant_ht for line in self.lignes.all())
        subtotal_after_remise = self.sous_total - self.remise
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()
    
    @property
    def montant_restant(self):
        return self.total - self.montant_paye
    
    @property
    def est_payee(self):
        return self.montant_restant <= 0


class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.article.nom} - {self.quantite} x {self.prix_unitaire}"
    
    @property
    def montant_ht(self):
        return self.quantite * self.prix_unitaire
    
    @property
    def montant_remise(self):
        return self.montant_ht * (self.taux_remise / 100)
    
    @property
    def montant_total(self):
        return self.montant_ht - self.montant_remise


class Proforma(models.Model):
    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
        ('invoiced', 'Facturé'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_validite = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='draft')
    
    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Proforma {self.numero} - {self.client.nom_complet}"
    
    def calculate_totals(self):
        self.sous_total = sum(line.montant_ht for line in self.lignes.all())
        subtotal_after_remise = self.sous_total - self.remise
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()
    
    def convert_to_facture(self):
        """Convertir le proforma en facture"""
        if self.statut != 'accepted':
            raise ValueError("Le proforma doit être accepté pour être converti en facture")
        
        # Créer la facture
        facture = Facture.objects.create(
            numero=Facture.generate_numero(),
            client=self.client,
            date_facturation=timezone.now().date(),
            taux_tva=self.taux_tva,
            sous_total=self.sous_total,
            montant_tva=self.montant_tva,
            total=self.total,
            cree_par=self.cree_par,
            notes=f"Converti depuis le proforma {self.numero}"
        )
        
        # Copier les lignes
        for ligne_proforma in self.lignes.all():
            LigneFacture.objects.create(
                facture=facture,
                article=ligne_proforma.article,
                description=ligne_proforma.description,
                quantite=ligne_proforma.quantite,
                prix_unitaire=ligne_proforma.prix_unitaire,
                taux_remise=ligne_proforma.taux_remise
            )
        
        # Marquer le proforma comme facturé
        self.statut = 'invoiced'
        self.save()
        
        return facture


class LigneProforma(models.Model):
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.article.nom} - {self.quantite} x {self.prix_unitaire}"
    
    @property
    def montant_ht(self):
        return self.quantite * self.prix_unitaire
    
    @property
    def montant_remise(self):
        return self.montant_ht * (self.taux_remise / 100)
    
    @property
    def montant_total(self):
        return self.montant_ht - self.montant_remise


class Avoir(models.Model):
    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('refunded', 'Remboursé'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    facture_origine = models.ForeignKey(Facture, on_delete=models.SET_NULL, null=True, blank=True, related_name='avoirs')
    ticket_origine = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='avoirs')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_avoir = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='draft')
    
    # Motif obligatoire pour l'avoir
    motif = models.TextField(help_text="Motif obligatoire de l'avoir")
    
    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Avoir {self.numero} - Facture {self.facture_originale.numero}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        self.sous_total = sum(line.montant_ht for line in self.lignes.all())
        subtotal_after_remise = self.sous_total - self.remise
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()
    
    def apply_refund(self):
        """Appliquer le remboursement à la facture originale"""
        if self.statut != 'accepted':
            raise ValueError("L'avoir doit être accepté pour être appliqué")
        
        facture = self.facture_originale
        facture.montant_paye -= self.total
        if facture.montant_paye < 0:
            facture.montant_paye = Decimal('0.00')
        facture.save()
        
        self.statut = 'refunded'
        self.save()


class LigneAvoir(models.Model):
    avoir = models.ForeignKey(Avoir, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.article.nom} - {self.quantite} x {self.prix_unitaire}"
    
    @property
    def montant_ht(self):
        return self.quantite * self.prix_unitaire
    
    @property
    def montant_remise(self):
        return self.montant_ht * (self.taux_remise / 100)
    
    @property
    def montant_total(self):
        return self.montant_ht - self.montant_remise


class Ticket(models.Model):
    """Modèle pour stocker les tickets des différents modules"""
    MODULE_CHOICES = [
        ('hotel', 'Hôtel'),
        ('restaurant', 'Restaurant'),
        ('caisse', 'Caisse'),
        ('piscine', 'Piscine'),
        ('autre', 'Autre'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    date_creation = models.DateTimeField(default=timezone.now)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    
    PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('moov_money', 'Moov Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('carte_bancaire', 'Carte Bancaire'),
        ('carte', 'Carte Bancaire'), # Alias pour compatibilité
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('autre', 'Autre'),
    ]

    # Informations Paiement
    mode_paiement = models.CharField(max_length=50, choices=PAIEMENT_CHOICES, default='especes')
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Informations du ticket
    contenu = models.TextField(help_text="Contenu détaillé du ticket")
    imprime = models.BooleanField(default=False)
    date_impression = models.DateTimeField(blank=True, null=True)
    est_duplicata = models.BooleanField(default=False, help_text="Indique si c'est une réimpression")
    
    # Référence à l'objet original
    objet_id = models.IntegerField(blank=True, null=True, help_text="ID de l'objet dans le module d'origine")
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Ticket {self.numero} - {self.get_module_display()}"
    
    def mark_as_printed(self):
        self.imprime = True
        self.date_impression = timezone.now()
        self.save()
    
    def mark_as_duplicata(self):
        self.est_duplicata = True
        self.save()

    @property
    def monnaie_rendue(self):
        """Calculer la monnaie rendue (si payé > total)"""
        try:
            if self.montant_paye > self.montant_total:
                return self.montant_paye - self.montant_total
            return 0
        except:
            return 0


# Méthodes utilitaires pour la génération de numéros
def generate_facture_numero():
    """Générer un numéro de facture unique"""
    prefix = "FCT"
    last_facture = Facture.objects.filter(numero__startswith=prefix).order_by('-id').first()
    
    if last_facture:
        try:
            last_number = int(last_facture.numero.replace(prefix + "-", ""))
            new_number = last_number + 1
        except (ValueError, AttributeError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:06d}"


def generate_ticket_numero():
    """Générer un numéro de ticket unique"""
    prefix = "TC"
    # Format: TC-YYYYMMDD-XXXX ou juste TC-XXXXXX
    # On va faire simple: TC-XXXXXX
    last_ticket = Ticket.objects.filter(numero__startswith=prefix).order_by('-id').first()
    
    if last_ticket:
        try:
            # On suppose le format TC-000001
            parts = last_ticket.numero.split('-')
            if len(parts) == 2 and parts[1].isdigit():
                last_number = int(parts[1])
                new_number = last_number + 1
            else:
                # Fallback si le format est différent (ex: random string du restaurant)
                new_number = Ticket.objects.count() + 1
        except (ValueError, AttributeError):
            new_number = Ticket.objects.count() + 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:06d}"


def generate_proforma_numero():
    """Générer un numéro de proforma unique"""
    prefix = "PROF"
    last_proforma = Proforma.objects.filter(numero__startswith=prefix).order_by('-id').first()
    
    if last_proforma:
        try:
            last_number = int(last_proforma.numero.replace(prefix + "-", ""))
            new_number = last_number + 1
        except (ValueError, AttributeError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:06d}"


def generate_avoir_numero():
    """Générer un numéro d'avoir unique"""
    prefix = "AVOIR"
    last_avoir = Avoir.objects.filter(numero__startswith=prefix).order_by('-id').first()
    
    if last_avoir:
        try:
            last_number = int(last_avoir.numero.replace(prefix + "-", ""))
            new_number = last_number + 1
        except (ValueError, AttributeError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:06d}"


# Ajouter les méthodes de génération aux modèles
Facture.generate_numero = staticmethod(generate_facture_numero)
Proforma.generate_numero = staticmethod(generate_proforma_numero)
Avoir.generate_numero = staticmethod(generate_avoir_numero)