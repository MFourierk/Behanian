from django.db import models
from django.contrib.auth.models import User

class Chambre(models.Model):
    """Modèle pour les chambres de l'hôtel"""
    
    TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('superieure', 'Supérieure'),
        ('suite', 'Suite'),
        ('vip', 'VIP'),
    ]
    
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('occupee', 'Occupée'),
        ('maintenance', 'Maintenance'),
        ('reservation', 'Réservation'),
    ]
    
    numero = models.CharField(max_length=10, unique=True, verbose_name="Numéro")
    type_chambre = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    etage = models.IntegerField(verbose_name="Étage")
    capacite = models.IntegerField(default=2, verbose_name="Capacité (personnes)")
    prix_nuit = models.IntegerField(verbose_name="Prix Nuitée (FCFA)")
    prix_sejour = models.IntegerField(default=0, verbose_name="Prix Séjour (FCFA)")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible', verbose_name="Statut")
    
    # Détails & Image
    image = models.ImageField(upload_to='chambres/', blank=True, null=True, verbose_name="Photo")
    description = models.TextField(blank=True, null=True, verbose_name="Description détaillée")

    # Équipements
    wifi = models.BooleanField(default=True, verbose_name="WiFi")
    climatisation = models.BooleanField(default=True, verbose_name="Climatisation")
    television = models.BooleanField(default=True, verbose_name="Télévision")
    minibar = models.BooleanField(default=False, verbose_name="Minibar")
    machine_a_cafe = models.BooleanField(default=False, verbose_name="Machine à café")
    baignoire = models.BooleanField(default=False, verbose_name="Baignoire")
    coffre_fort = models.BooleanField(default=False, verbose_name="Coffre-fort")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chambre"
        verbose_name_plural = "Chambres"
        ordering = ['numero']
    
    def __str__(self):
        return f"Chambre {self.numero} - {self.get_type_chambre_display()}"


class Client(models.Model):
    """Modèle pour les clients de l'hôtel"""
    
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    piece_identite = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pièce d'identité")
    numero_piece = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro de pièce")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    nationalite = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nationalité")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pays")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
    def get_nom_complet(self):
        return self.nom_complet


class Reservation(models.Model):
    """Modèle pour les réservations"""
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte Bancaire'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
    ]

    TYPE_SEJOUR_CHOICES = [
        ('nuitee', 'Nuitée'),
        ('long_sejour', 'Long Séjour'),
    ]

    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, verbose_name="Chambre")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Client")
    
    date_arrivee = models.DateField(verbose_name="Date d'arrivée")
    date_depart = models.DateField(verbose_name="Date de départ")
    type_sejour = models.CharField(max_length=20, choices=TYPE_SEJOUR_CHOICES, default='nuitee', verbose_name="Type de Séjour")
    
    # Voyage Info
    nombre_adultes = models.IntegerField(default=1, verbose_name="Adultes")
    nombre_enfants = models.IntegerField(default=0, verbose_name="Enfants")
    provenance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Provenance")
    destination = models.CharField(max_length=100, blank=True, null=True, verbose_name="Destination")
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    
    prix_total = models.IntegerField(verbose_name="Prix total (FCFA)")
    avance = models.IntegerField(default=0, verbose_name="Avance payée (FCFA)")
    mode_paiement = models.CharField(max_length=20, choices=PAIEMENT_CHOICES, default='especes', verbose_name="Mode de Paiement")
    
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    
    creee_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Créée par")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Réservation {self.id} - {self.chambre.numero} - {self.client.get_nom_complet()}"
    
    def get_montant_restant(self):
        return self.prix_total - self.avance

    def get_prix_reel(self):
        """
        Calcule le prix basé sur la durée réelle du séjour (jusqu'à aujourd'hui).
        Utilisé pour le Check-out anticipé ou retardé.
        """
        if self.statut != 'en_cours':
            return self.prix_total
            
        from django.utils import timezone
        today = timezone.now().date()
        
        # Calcul du nombre de nuits passées
        # Si date_arrivee > today (ne devrait pas arriver), 0
        # Si date_arrivee == today, on compte 1 nuit minimum
        if self.date_arrivee > today:
            duree = 0
        else:
            duree = (today - self.date_arrivee).days
            
        if duree < 1:
            duree = 1
            
        # Recalcul du prix
        # On utilise le prix de la chambre actuel
        prix_reel = duree * self.chambre.prix_nuit
        return prix_reel

    def get_montant_services(self):
        """Calcule le total des services/consommations"""
        return sum(c.total for c in self.consommations.all())

    def get_total_general(self):
        """Prix hébergement + Services"""
        return self.get_prix_reel() + self.get_montant_services()

    def get_montant_restant_reel(self):
        """Reste à payer basé sur le temps passé et les services"""
        return self.get_total_general() - self.avance


class Consommation(models.Model):
    TYPES = [
        ('bar', 'Bar'),
        ('restaurant', 'Restaurant'),
        ('espace', 'Espace Location'),
        ('autre', 'Autre Service'),
    ]
    
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='consommations')
    type_service = models.CharField(max_length=20, choices=TYPES)
    
    # Liens optionnels vers les services
    boisson = models.ForeignKey('bar.BoissonBar', on_delete=models.SET_NULL, null=True, blank=True)
    plat = models.ForeignKey('restaurant.PlatMenu', on_delete=models.SET_NULL, null=True, blank=True)
    espace = models.ForeignKey('espaces_evenementiels.EspaceEvenementiel', on_delete=models.SET_NULL, null=True, blank=True)
    
    nom = models.CharField(max_length=200, verbose_name="Désignation")
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Consommation"
        verbose_name_plural = "Consommations"
        ordering = ['-date_ajout']
        
    def __str__(self):
        return f"{self.nom} ({self.quantite}) - Chambre {self.reservation.chambre.numero}"
        
    @property
    def total(self):
        return self.quantite * self.prix_unitaire
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Gestion du stock pour le Bar lors de la création
        if is_new and self.type_service == 'bar' and self.boisson:
            from bar.models import MouvementStockBar
            # On enregistre une sortie de stock
            MouvementStockBar.objects.create(
                boisson=self.boisson,
                type_mouvement='sortie',
                quantite=self.quantite,
                commentaire=f"Conso Chambre {self.reservation.chambre.numero}"
            )
