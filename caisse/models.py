from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class CaisseSession(models.Model):
    """Session de caisse — ouverture à clôture."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='caisse_sessions')
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)

    # Fond de caisse
    fond_caisse = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    fond_caisse_reel = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'), help_text="Fond compté à la clôture")

    # Totaux calculés à la clôture
    total_especes = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_mobile  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_carte   = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_virement= models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_general = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # Prélèvement banque effectué lors de la clôture
    prelevement_banque = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        statut = "Ouverte" if self.is_open else "Clôturée"
        return f"Caisse {self.user.get_full_name() or self.user.username} — {self.opened_at.strftime('%d/%m/%Y %H:%M')} [{statut}]"

    @property
    def duree(self):
        fin = self.closed_at or timezone.now()
        delta = fin - self.opened_at
        h, m = divmod(delta.seconds // 60, 60)
        return f"{h}h{m:02d}"


class MouvementCaisse(models.Model):
    """Chaque opération financière enregistrée en caisse."""

    TYPE_CHOICES = [
        ('encaissement', 'Encaissement'),
        ('versement',    'Versement module → Caisse'),
        ('prelevement',  'Prélèvement banque'),
        ('depense',      'Dépense / Décaissement'),
        ('remboursement','Remboursement client'),
        ('ajustement',   'Ajustement caisse'),
        ('fond_caisse',  'Fond de caisse'),
    ]

    MODULE_CHOICES = [
        ('hotel',       'Hôtel'),
        ('restaurant',  'Restaurant'),
        ('cave',        'Cave / Bar'),
        ('piscine',     'Piscine'),
        ('espaces',     'Espaces Événementiels'),
        ('caisse',      'Caisse'),
        ('banque',      'Banque'),
        ('autre',       'Autre'),
    ]

    MODE_CHOICES = [
        ('especes',       'Espèces'),
        ('mobile_money',  'Mobile Money'),
        ('orange_money',  'Orange Money'),
        ('wave',          'Wave'),
        ('carte_bancaire','Carte Bancaire'),
        ('virement',      'Virement'),
        ('cheque',        'Chèque'),
        ('autre',         'Autre'),
    ]

    session   = models.ForeignKey(CaisseSession, on_delete=models.CASCADE, related_name='mouvements', null=True, blank=True)
    type      = models.CharField(max_length=20, choices=TYPE_CHOICES)
    module    = models.CharField(max_length=20, choices=MODULE_CHOICES, default='caisse')
    montant   = models.DecimalField(max_digits=12, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, default='especes')
    description = models.CharField(max_length=300, blank=True)
    reference   = models.CharField(max_length=100, blank=True, help_text="N° ticket, facture, bon…")
    date        = models.DateTimeField(default=timezone.now)
    cree_par    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mouvements_caisse')
    valide      = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} — {self.montant} F — {self.date.strftime('%d/%m/%Y %H:%M')}"

    @property
    def est_entree(self):
        return self.type in ('encaissement', 'versement', 'fond_caisse', 'ajustement')

    @property
    def est_sortie(self):
        return self.type in ('prelevement', 'depense', 'remboursement')


class PrelevementBanque(models.Model):
    """Enregistrement des prélèvements vers la banque."""
    session     = models.ForeignKey(CaisseSession, on_delete=models.CASCADE, related_name='prelevements', null=True, blank=True)
    montant     = models.DecimalField(max_digits=12, decimal_places=2)
    date        = models.DateTimeField(default=timezone.now)
    banque      = models.CharField(max_length=100, blank=True, help_text="Nom de la banque")
    reference   = models.CharField(max_length=100, blank=True, help_text="N° bordereau")
    notes       = models.TextField(blank=True)
    cree_par    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    valide      = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Prélèvement banque {self.montant} F — {self.date.strftime('%d/%m/%Y')}"
