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
        try:
            return self.nom
        except Exception:
            return f'Article #{self.pk}'

    @property
    def nom(self):
        """Retourne le nom de l'objet lié."""
        obj = self.content_object
        if obj is None:
            return f'Article #{self.pk} (objet supprimé)'
        return getattr(obj, 'nom', str(obj))

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
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('impayee', 'Impayée'),
        ('partielle', 'Part. payée'),
        ('annulee', 'Annulée'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_facturation = models.DateField(default=timezone.now)
    date_echeance = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))

    # Champs de paiement
    montant_paye = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    date_paiement = models.DateTimeField(blank=True, null=True)
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Facture {self.numero} - {self.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        # montant_total applique la remise ligne (taux_remise) — montant_ht ne l'applique pas
        self.sous_total = sum(line.montant_total for line in self.lignes.all())
        subtotal_after_remise = max(Decimal('0.00'), self.sous_total - self.remise)
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()

    @property
    def montant_restant(self):
        return self.total - self.montant_paye
    
    @property
    def est_payee(self):
        return self.montant_restant <= 0

    def marquer_envoyee(self):
        if self.statut != 'brouillon':
            raise ValueError(f"Seul un brouillon peut être envoyé (statut actuel : {self.get_statut_display()}).")
        self.statut = 'envoyee'
        self.save(update_fields=['statut'])

    def marquer_payee(self):
        if self.statut == 'annulee':
            raise ValueError("Une facture annulée ne peut pas être marquée payée.")
        self.statut = 'payee'
        self.montant_paye = self.total
        self.date_paiement = timezone.now()
        self.save(update_fields=['statut', 'montant_paye', 'date_paiement'])

    def annuler(self):
        if self.statut == 'payee':
            raise ValueError("Une facture payée ne peut pas être annulée directement — émettez un avoir.")
        self.statut = 'annulee'
        self.save(update_fields=['statut'])


class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=200, blank=True, verbose_name='Désignation')
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=3)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        nom = self.designation or (self.article.nom if self.article else 'Ligne')
        return f"{nom} - {self.quantite} x {self.prix_unitaire}"
    
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
        ('en_attente', 'En attente'),
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('acceptee', 'Acceptée'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('annulee', 'Annulée'),
        ('convertie', 'Convertie'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_validite = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))

    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Proforma {self.numero} - {self.client.nom_complet}"
    
    def calculate_totals(self):
        self.sous_total = sum(line.montant_total for line in self.lignes.all())
        subtotal_after_remise = max(Decimal('0.00'), self.sous_total - self.remise)
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()

    def convert_to_facture(self):
        """Convertir le proforma en facture"""
        if self.statut not in ('acceptee', 'validee'):
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
        
        # Copier les lignes (designation incluse — champ libre B2B)
        for ligne_proforma in self.lignes.all():
            LigneFacture.objects.create(
                facture=facture,
                article=ligne_proforma.article,
                designation=ligne_proforma.designation,
                description=ligne_proforma.description,
                quantite=ligne_proforma.quantite,
                prix_unitaire=ligne_proforma.prix_unitaire,
                taux_remise=ligne_proforma.taux_remise,
            )
        
        # Marquer le proforma comme converti
        self.statut = 'convertie'
        self.save()
        
        return facture


class LigneProforma(models.Model):
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=200, blank=True, verbose_name='Désignation')
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=3)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        nom = self.designation or (self.article.nom if self.article else 'Ligne')
        return f"{nom} - {self.quantite} x {self.prix_unitaire}"
    
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
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('traitee', 'Traitée'),
        ('rembourse', 'Remboursé'),
        ('annulee', 'Annulée'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    facture_origine = models.ForeignKey(Facture, on_delete=models.SET_NULL, null=True, blank=True, related_name='avoirs')
    ticket_origine = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='avoirs')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    date_avoir = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Motif obligatoire pour l'avoir
    motif = models.TextField(help_text="Motif obligatoire de l'avoir")
    
    # Champs de calcul
    sous_total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    remise = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('20.00'))
    montant_tva = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.00'))
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        origine = self.facture_origine.numero if self.facture_origine else "—"
        return f"Avoir {self.numero} — {self.client.nom if self.client else origine}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        self.sous_total = sum(line.montant_total for line in self.lignes.all())
        subtotal_after_remise = max(Decimal('0.00'), self.sous_total - self.remise)
        self.montant_tva = subtotal_after_remise * (self.taux_tva / 100)
        self.total = subtotal_after_remise + self.montant_tva
        self.save()

    def apply_refund(self):
        """Appliquer l'avoir à la facture d'origine.
        L'avoir diminue ce que le client doit (réduit facture.total),
        pas l'encaissement déjà reçu (montant_paye reste intact).
        """
        if self.statut != 'accepte':
            raise ValueError("L'avoir doit être accepté pour être appliqué")

        if self.facture_origine:
            facture = self.facture_origine
            facture.total = max(Decimal('0.00'), facture.total - self.total)
            # Mise à jour du statut en fonction du solde restant
            if facture.total <= facture.montant_paye:
                facture.statut = 'payee'
            elif facture.montant_paye > 0:
                facture.statut = 'partielle'
            facture.save(update_fields=['total', 'statut'])

        self.statut = 'rembourse'
        self.save(update_fields=['statut'])


class LigneAvoir(models.Model):
    avoir = models.ForeignKey(Avoir, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=200, blank=True, verbose_name='Désignation')
    description = models.TextField(blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=3)
    taux_remise = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        nom = self.designation or (self.article.nom if self.article else 'Ligne')
        return f"{nom} - {self.quantite} x {self.prix_unitaire}"
    
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
        ('cave', 'Cave'),
        ('espace', 'Espaces Événementiels'),
        ('autre', 'Autre'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    date_creation = models.DateTimeField(default=timezone.now)
    montant_total = models.DecimalField(max_digits=10, decimal_places=3)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    
    PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('mixte', 'Mixte'),
        ('mobile_money', 'Mobile Money'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('moov_money', 'Moov Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('carte_bancaire', 'Carte Bancaire'),
        ('carte', 'Carte Bancaire'), # Alias pour compatibilité
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('cave', 'Cave'),
        ('autre', 'Autre'),
    ]

    # Informations Paiement
    mode_paiement = models.CharField(max_length=50, choices=PAIEMENT_CHOICES, default='especes')
    montant_paye = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    # Portion espèces d'un paiement mixte (espèces + mobile money).
    # 0 = paiement pur (espèces OU mobile). > 0 = paiement mixte.
    montant_especes = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Informations du ticket
    contenu = models.TextField(help_text="Contenu détaillé du ticket")
    imprime = models.BooleanField(default=False)
    date_impression = models.DateTimeField(blank=True, null=True)
    est_duplicata = models.BooleanField(default=False, help_text="Indique si c'est une réimpression")
    
    # Référence à l'objet original
    objet_id = models.IntegerField(blank=True, null=True, help_text="ID de l'objet dans le module d'origine")

    # Facture globale dans laquelle ce ticket a été regroupé (multi-services B2B)
    # Quand ce champ est renseigné, le ticket est exclu des totaux caisse (le paiement
    # passe par la facture) — évite le double-comptage CA.
    facture_consolidee = models.ForeignKey(
        'Facture',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets_consolides',
        help_text="Facture globale regroupant ce ticket (exclut du CA caisse)",
    )
    
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


class LignePaiement(models.Model):
    """Détail des modes de paiement d'un ticket (multi-mode : Wave + Orange + Espèces…).
    Créée pour chaque ticket à partir du commit 3aaca67+.
    Anciens tickets sans lignes : se référer à Ticket.mode_paiement / montant_especes.
    """
    MODES = [
        ('especes',       'Espèces'),
        ('wave',          'Wave'),
        ('orange_money',  'Orange Money'),
        ('mtn_money',     'MTN Mobile Money'),
        ('moov_money',    'Moov Money'),
        ('mobile_money',  'Mobile Money'),
        ('carte_bancaire','Carte Bancaire'),
        ('cheque',        'Chèque'),
        ('virement',      'Virement'),
        ('cave',          'Cave (consommation bar)'),
        ('autre',         'Autre'),
    ]
    ticket        = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='lignes_paiement')
    mode_paiement = models.CharField(max_length=30, choices=MODES)
    montant       = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        app_label = 'facturation'
        ordering  = ['id']

    def __str__(self):
        return f"{self.get_mode_paiement_display()} {self.montant} F — Ticket {self.ticket_id}"


# Méthodes utilitaires pour la génération de numéros
def generate_facture_numero():
    """Générer un numéro de facture unique — format FAC-YYYY-XXXX (atomique)"""
    from django.utils import timezone as tz
    from django.db import transaction
    annee = tz.now().year
    with transaction.atomic():
        last = (Facture.objects.select_for_update()
                .filter(numero__startswith=f'FAC-{annee}-')
                .order_by('numero').last())
        if last:
            try:
                seq = int(last.numero.split('-')[-1]) + 1
            except (ValueError, AttributeError):
                seq = Facture.objects.count() + 1
        else:
            seq = 1
        return f'FAC-{annee}-{seq:04d}'


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
    """Générer un numéro de proforma unique — format PRO-YYYY-XXXX (atomique)"""
    from django.utils import timezone as tz
    from django.db import transaction
    annee = tz.now().year
    with transaction.atomic():
        last = (Proforma.objects.select_for_update()
                .filter(numero__startswith=f'PRO-{annee}-')
                .order_by('numero').last())
        if last:
            try:
                seq = int(last.numero.split('-')[-1]) + 1
            except (ValueError, AttributeError):
                seq = Proforma.objects.count() + 1
        else:
            seq = 1
        return f'PRO-{annee}-{seq:04d}'


def generate_avoir_numero():
    """Générer un numéro d'avoir unique — format AVO-YYYY-XXXX (atomique)"""
    from django.utils import timezone as tz
    from django.db import transaction
    annee = tz.now().year
    with transaction.atomic():
        last = (Avoir.objects.select_for_update()
                .filter(numero__startswith=f'AVO-{annee}-')
                .order_by('numero').last())
        if last:
            try:
                seq = int(last.numero.split('-')[-1]) + 1
            except (ValueError, AttributeError):
                seq = Avoir.objects.count() + 1
        else:
            seq = 1
        return f'AVO-{annee}-{seq:04d}'


# Ajouter les méthodes de génération aux modèles
Facture.generate_numero = staticmethod(generate_facture_numero)
Proforma.generate_numero = staticmethod(generate_proforma_numero)
Avoir.generate_numero = staticmethod(generate_avoir_numero)


class Reglement(models.Model):
    """Journal des encaissements sur une facture (une ligne par versement)."""
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='reglements')
    date = models.DateField(default=timezone.now)
    montant = models.DecimalField(max_digits=10, decimal_places=3)
    mode_paiement = models.CharField(max_length=30, choices=LignePaiement.MODES)
    reference = models.CharField(max_length=100, blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_creation']

    def __str__(self):
        return f"Règlement {self.montant} F — {self.facture.numero} ({self.get_mode_paiement_display()})"
