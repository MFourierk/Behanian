from django.db import models
from django.contrib.auth.models import User

class EspaceEvenementiel(models.Model):
    """Espaces louables pour événements"""
    TYPE_ESPACE = [
        ('salle_conference', 'Salle de conférence'),
        ('salle_reception', 'Salle de réception'),
        ('espace_exterieur', 'Espace extérieur'),
        ('jardin', 'Jardin'),
        ('terrasse', 'Terrasse'),
    ]
    
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservee', 'Réservée'),
        ('occupee', 'Occupée'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom de l'espace")
    type_espace = models.CharField(max_length=50, choices=TYPE_ESPACE, verbose_name="Type")
    capacite = models.IntegerField(verbose_name="Capacité (personnes)")
    prix_jour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix par jour (FCFA)", default=0)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Superficie (m²)")
    
    # Équipements
    projecteur = models.BooleanField(default=False, verbose_name="Projecteur")
    wifi = models.BooleanField(default=False, verbose_name="WiFi")
    climatisation = models.BooleanField(default=False, verbose_name="Climatisation")
    sonorisation = models.BooleanField(default=False, verbose_name="Sonorisation")
    decoration = models.BooleanField(default=False, verbose_name="Décoration")
    eclairage = models.BooleanField(default=False, verbose_name="Éclairage")
    tentes = models.BooleanField(default=False, verbose_name="Tentes")
    parking = models.BooleanField(default=False, verbose_name="Parking")
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible', verbose_name="Statut")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='espaces/', blank=True, null=True, verbose_name="Photo")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Espace Location"
        verbose_name_plural = "Espaces Location"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.capacite} pers."


class ReservationEspace(models.Model):
    """Réservations d'espaces événementiels"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    TYPE_CLIENT = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('heberge', 'Résident hôtel'),
    ]
    
    espace = models.ForeignKey(EspaceEvenementiel, on_delete=models.CASCADE, verbose_name="Espace")
    
    # Informations client
    nom_client = models.CharField(max_length=100, verbose_name="Nom du client")
    type_client = models.CharField(max_length=20, choices=TYPE_CLIENT, verbose_name="Type de client")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    # Détails réservation
    type_evenement = models.CharField(max_length=100, verbose_name="Type d'événement")
    date_debut = models.DateTimeField(verbose_name="Date et heure de début")
    date_fin = models.DateTimeField(verbose_name="Date et heure de fin")
    nombre_personnes = models.IntegerField(verbose_name="Nombre de personnes")
    
    # Tarification
    prix_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total (FCFA)")
    remise = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Remise (FCFA)")
    avance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Avance payée (FCFA)")
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    
    # Lien hôtel si résident
    reservation_hotel = models.ForeignKey(
        'hotel.Reservation', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Réservation hôtel",
        related_name='locations_espace'
    )
    
    creee_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Créée par")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.nom_client} - {self.espace.nom} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    @property
    def duree_jours(self):
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            return round(delta.total_seconds() / 86400, 1)
        return 0

    @property
    def montant_net(self):
        return self.prix_total - self.remise

    def get_montant_restant(self):
        return self.prix_total - self.remise - self.avance