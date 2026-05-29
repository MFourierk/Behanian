# Manuel Utilisateur — Complexe Hôtelier BEHANIAN
**Version 1.0 — Mai 2026**

---

## Table des matières

1. [Introduction et connexion](#1-introduction-et-connexion)
2. [Navigation générale](#2-navigation-générale)
3. [Directeur Général & Manager](#3-directeur-général--manager)
4. [Réceptionniste & Responsable Hôtel](#4-réceptionniste--responsable-hôtel)
5. [Chef caissier(e) & Caissier(e)](#5-chef-caissierre--caissierre)
6. [Manager Cuisine & Cuisinier(e)](#6-manager-cuisine--cuisinière)
7. [Serveuse / Serveur](#7-serveuse--serveur)
8. [Piscine & Espaces Événementiels](#8-piscine--espaces-événementiels)
9. [Facturation](#9-facturation)
10. [Questions fréquentes](#10-questions-fréquentes)

---

## 1. Introduction et connexion

### Qu'est-ce que le logiciel Behanian ?

Le logiciel Behanian est le système de gestion intégré du Complexe Hôtelier Behanian. Il regroupe dans une seule application tous les services : hôtel, restaurant, cuisine, cave, piscine, espaces événementiels, caisse et facturation.

Chaque membre du personnel accède uniquement aux modules correspondant à son poste.

### Se connecter

1. Ouvrez votre navigateur (Chrome, Firefox ou Edge recommandé)
2. Allez sur l'adresse du logiciel fournie par votre responsable
3. Entrez votre **identifiant** et votre **mot de passe**
4. Cliquez sur **Se connecter**

> **Mot de passe oublié ?** Contactez votre Manager ou le Directeur pour une réinitialisation.

### Se déconnecter

Cliquez sur l'icône de déconnexion (→) en bas à gauche de la barre latérale.  
**Important :** déconnectez-vous toujours en quittant votre poste.

---

## 2. Navigation générale

### La barre latérale (menu de gauche)

Après connexion, vous voyez la barre latérale à gauche avec les modules auxquels vous avez accès. Cliquez sur un module pour y accéder.

| Icône | Module |
|-------|--------|
| 📊 | Dashboard (accueil) |
| 👑 | Vue Direction *(managers uniquement)* |
| 🏨 | Hôtel |
| 🍴 | Restaurant |
| 🍽️ | Cuisine |
| 🍷 | Cave |
| 🏊 | Piscine |
| 📅 | Espaces Événementiels |
| 📄 | Facturation |
| 💰 | Caisse |
| ⚙️ | Paramétrage *(managers uniquement)* |
| 🔧 | Administration *(superadmin uniquement)* |

**Réduire le menu :** cliquez sur la flèche `<` en haut du menu pour gagner de la place.  
**Sur mobile :** appuyez sur le bouton ☰ en haut pour ouvrir le menu.

### Le Dashboard (accueil)

Le Dashboard est la première page après connexion. Il affiche :
- **CA du jour** et variation par rapport à hier
- **Taux d'occupation** de l'hôtel
- **Réservations** actives et en attente
- **Alertes stock** (ingrédients en rupture)
- **État de la caisse** (ouverte ou fermée)
- **Tickets récents** des 8 dernières transactions

Ces chiffres se mettent à jour automatiquement toutes les 30 secondes.

---

## 3. Directeur Général & Manager

### Votre rôle

Vous avez accès à **tous les modules** du logiciel. Votre espace principal est la **Vue Direction**, accessible via l'icône 👑 dans le menu.

### Vue Direction

La Vue Direction est votre tableau de bord consolidé. Elle se compose de :

#### Les KPI (indicateurs clés)
En haut de la page, 6 cartes affichent en temps réel :
- **CA du jour** — chiffre d'affaires de la journée en cours
- **Taux d'occupation** — % de chambres occupées
- **Réservations** — nombre de séjours actifs
- **Alertes Cave** — articles en rupture ou stock bas
- **Alertes Cuisine** — ingrédients en rupture ou stock bas
- **Fond de caisse** — solde théorique de la session centrale

#### Onglet Vue globale
Contient 3 sections :

**Caisse du jour**  
Tableau de toutes les sessions ouvertes aujourd'hui avec :
- Fond initial, espèces encaissées, solde théorique
- Fond réel compté, écart
- Statut (ouverte / clôturée)

**CA par module**  
Graphique en barres du chiffre d'affaires ventilé par module (Hôtel, Restaurant, Cave, Piscine, Espaces).

**Tickets récents**  
Les 8 dernières transactions avec montant, mode de paiement et module.

**Gestion des stocks**  
Accès direct à l'état du stock Cave et Cuisine à date.

#### Onglet Mouvements
Historique des 40 derniers mouvements de stock (Cave + Cuisine) avec filtres par source, type et nom d'article.

### Gérer le personnel

Accédez à **Paramétrage → Personnel** via l'icône ⚙️.

#### Ajouter un membre du personnel
1. Cliquez sur **Nouveau membre**
2. Remplissez : Prénom, Nom, Identifiant de connexion, Mot de passe, Groupe (poste)
3. Cliquez sur **Créer**

> **Important :** si un groupe n'existe pas encore, cliquez d'abord sur **Initialiser les postes** pour créer automatiquement tous les groupes métier.

#### Groupes disponibles

| Groupe | Accès |
|--------|-------|
| Directeur Général | Tous les modules |
| Manager Général(e) | Tous les modules |
| Responsable Hôtel | Hôtel, Facturation |
| Réceptionniste | Hôtel |
| Chef caissier(e) | Caisse, tous les modules en lecture |
| Caissier(e) | Caisse |
| Manager Cuisine | Cuisine, Restaurant |
| Cuisinier(e) | Cuisine |
| Serveuse/Serveur | Restaurant |
| Agent de Sécurité | Accès limité |

#### Modifier un membre
1. Cliquez sur ✏️ en face du membre
2. Modifiez les informations souhaitées
3. Cliquez sur **Sauvegarder**

#### Réinitialiser un mot de passe
1. Cliquez sur 🔑 en face du membre
2. Entrez le nouveau mot de passe
3. Confirmez

#### Désactiver / Réactiver un compte
Cliquez sur le bouton de statut (✅ ou 🔴) en face du membre. Un compte désactivé ne peut plus se connecter.

#### Supprimer un compte
Cliquez sur 🗑️. Attention : l'action est irréversible.

> **Le compte superadmin est protégé.** Personne ne peut le modifier, désactiver ou supprimer depuis cette interface. Seul l'administrateur système peut modifier ce compte via `/admin/`.

### Paramétrage des modules

Via ⚙️ **Paramétrage**, vous pouvez configurer :
- **Chambres** : ajouter, modifier, supprimer des chambres
- **Tables restaurant** : gérer les tables et leur capacité
- **Catégories restaurant** : organiser le menu par catégorie
- **Articles cave** : configurer les boissons et leurs tarifs
- **Espaces événementiels** : configurer les salles et équipements
- **Forfaits** : créer des forfaits (piscine VIP, packages hôtel)

---

## 4. Réceptionniste & Responsable Hôtel

### Vue d'ensemble du module Hôtel

Le tableau de bord Hôtel affiche :
- **Grille des chambres** avec statuts en couleur :
  - 🟢 Vert = Disponible
  - 🔴 Rouge = Occupée
  - 🟡 Jaune = Réservée
  - ⚫ Gris = En maintenance
- **Arrivées du jour**
- **Réservations en attente**
- **Revenus du jour**

### Créer une réservation

1. Cliquez sur **Nouvelle réservation**
2. Remplissez :
   - **Client** : nom, prénom, téléphone, pièce d'identité
   - **Chambre** : sélectionnez dans la liste des disponibles
   - **Dates** : arrivée et départ prévus
   - **Avance** : montant d'acompte éventuel
3. Cliquez sur **Créer la réservation**

La chambre passe automatiquement en statut **Réservée**.

### Check-in (arrivée d'un client)

#### Option 1 : Check-in sur réservation existante
1. Retrouvez la réservation dans la liste des arrivées du jour
2. Cliquez sur **Check-in**
3. Vérifiez et complétez les informations du client
4. Cliquez sur **Confirmer l'arrivée**
5. Imprimez la **fiche de police** si nécessaire

#### Option 2 : Check-in direct (client sans réservation)
1. Cliquez sur **Check-in direct**
2. Remplissez les informations client, la chambre et les dates
3. Cliquez sur **Enregistrer**

Après le check-in, la chambre passe en statut **Occupée**.

### Ajouter des consommations à une réservation

Pendant le séjour, un client peut consommer des services débités sur sa chambre :

1. Cliquez sur la réservation active
2. Cliquez sur **Ajouter une consommation**
3. Choisissez le type : Restauration / Boisson / Espace / Autre
4. Sélectionnez l'article et la quantité
5. Cliquez sur **Ajouter**

Les consommations s'accumulent et seront facturées au check-out.

### Check-out (départ d'un client)

1. Retrouvez la réservation dans la liste des séjours en cours
2. Cliquez sur **Check-out**
3. Vérifiez le **récapitulatif** :
   - Nuitées
   - Consommations
   - Total à payer
4. Choisissez le **mode de paiement** (espèces, carte, virement)
5. Cliquez sur **Encaisser et clôturer**
6. Imprimez le ticket de paiement
7. Cliquez sur **Finaliser** pour libérer la chambre

La chambre repasse automatiquement en statut **Disponible**.

### Gérer les chambres en maintenance

Si une chambre est hors service, changez son statut en **Maintenance** depuis le tableau de bord pour l'exclure des disponibilités.

---

## 5. Chef caissier(e) & Caissier(e)

### Principe de la caisse

Chaque journée commence par l'**ouverture** d'une session de caisse et se termine par sa **clôture**. Tous les paiements encaissés dans la journée sont enregistrés dans la session active.

### Ouvrir la caisse

1. Accédez au module **Caisse**
2. Cliquez sur **Ouvrir la caisse**
3. Choisissez le **type** :
   - *Caisse centrale* : caisse principale du complexe
   - *Caisse hôtel* : dédiée à la réception
   - *Caisse module* : pour un service spécifique
4. Entrez le **fond de caisse** (montant en espèces présent dans la caisse en début de journée)
5. Cliquez sur **Ouvrir**

> Une seule session centrale peut être ouverte à la fois.

### Tableau de bord de la caisse

Une fois la session ouverte, le tableau affiche :
- **Total encaissé** du jour par mode de paiement (espèces, carte, virement, chambre)
- **Mouvements** (entrées et sorties)
- **Prélèvements** banque de la journée
- **Sessions** ouvertes dans les différents modules

### Enregistrer un mouvement manuel

Pour enregistrer une **dépense** ou un **remboursement** non lié à une vente :

1. Cliquez sur **Nouveau mouvement**
2. Choisissez le type : *Dépense* / *Remboursement* / *Ajustement*
3. Entrez le montant et un motif
4. Cliquez sur **Enregistrer**

### Prélèvement banque

Quand vous transférez des espèces vers la banque en cours de journée :

1. Cliquez sur **Prélèvement banque**
2. Entrez le montant prélevé
3. Confirmez

Ce montant est déduit du solde espèces mais reste comptabilisé dans la journée.

### Clôturer la caisse

En fin de journée :

1. Cliquez sur **Clôturer la session**
2. Entrez le **fond réel compté** (ce qu'il y a physiquement dans la caisse)
3. Le logiciel calcule automatiquement l'**écart** entre fond théorique et réel
4. Ajoutez des notes si nécessaire
5. Cliquez sur **Clôturer**
6. Imprimez le **rapport de caisse**

> **Fond théorique** = Fond initial + Encaissements espèces - Dépenses espèces - Prélèvements banque

### Rapport de caisse

Le rapport imprimable détaille :
- Fond initial et fond final
- Total par mode de paiement
- Liste de tous les mouvements
- Prélèvements banque
- Écart et signature Chef caissier(e)

### Historique des sessions *(Chef caissier uniquement)*

Accédez à l'historique des 30 derniers jours via **Historique** pour consulter les sessions passées et leurs rapports.

### Forcer la clôture d'une session bloquante *(Chef caissier uniquement)*

Si une session d'un autre module bloque l'ouverture de la caisse centrale :

1. Dans le tableau de bord caisse, repérez la session bloquante
2. Cliquez sur **Forcer la clôture**
3. Confirmez

---

## 6. Manager Cuisine & Cuisinier(e)

### Vue d'ensemble du module Cuisine

Le module Cuisine gère les stocks d'ingrédients, les recettes (fiches techniques), les plats du menu, les commandes fournisseurs et les inventaires.

### Gestion des ingrédients

Accédez à **Cuisine → Stock** puis onglet **Ingrédients**.

#### Ajouter un ingrédient
1. Cliquez sur **Nouvel ingrédient**
2. Remplissez : Nom, Catégorie, Unité de stock, Unité de recette, Prix unitaire moyen, Seuil d'alerte
3. Cliquez sur **Enregistrer**

#### Modifier le stock d'un ingrédient
1. Cliquez sur **Mouvement de stock**
2. Choisissez : *Entrée* (réception) ou *Sortie* (consommation/perte)
3. Sélectionnez l'ingrédient, la quantité et le motif
4. Cliquez sur **Enregistrer**

#### Alertes de stock
Les ingrédients dont le stock est bas ou en rupture apparaissent en **rouge** ou **orange** dans la liste. Le nombre d'alertes est visible sur le Dashboard.

### Fiches techniques (recettes)

Une fiche technique est la recette standardisée d'un plat : elle liste les ingrédients, les quantités et calcule le coût de revient.

#### Créer une fiche technique
1. Allez dans **Cuisine → Fiches Techniques**
2. Cliquez sur **Nouvelle Fiche**
3. Remplissez :
   - **Nom** de la recette
   - **Catégorie** (entrée, plat principal, dessert...)
   - **Nombre de portions**
   - **Temps de préparation et cuisson**
   - **Description / méthode** de préparation
   - **Photo** (optionnel) : cliquez sur la zone rouge pour sélectionner une image
4. Ajoutez les **ingrédients** : cliquez sur **Ajouter un ingrédient**, choisissez l'ingrédient et la quantité
5. Le **coût de revient** se calcule automatiquement à droite
6. Cliquez sur **Créer la fiche**

#### Consulter une fiche
Cliquez sur le nom de la fiche pour voir le détail complet avec coût par portion et prix de vente suggéré (×3 du coût).

### Gestion des plats

Les plats sont les articles vendus au restaurant. Chaque plat est lié à une fiche technique.

#### Créer un plat
1. Allez dans **Cuisine → Plats**
2. Cliquez sur **Nouveau Plat**
3. Remplissez :
   - **Nom du plat**
   - **Catégorie** (menu)
   - **Prix de vente**
   - **Photo** : cliquez sur la zone rouge pour ajouter une photo
   - **Composition** : ajoutez les ingrédients (fiche technique intégrée)
4. Cliquez sur **Créer le plat**

Le plat est automatiquement synchronisé avec le menu du Restaurant.

#### Synchroniser les plats avec le Restaurant
Si des plats ne sont pas visibles au Restaurant, cliquez sur **Synchroniser avec le restaurant**.

### Bons de commande fournisseurs

Quand vous avez besoin de réapprovisionner les stocks :

1. Allez dans **Cuisine → Bons de commande**
2. Cliquez sur **Nouveau bon de commande**
3. Sélectionnez le **fournisseur**
4. Ajoutez les **ingrédients** et les **quantités** commandées
5. Cliquez sur **Enregistrer**

Le bon passe en statut **En attente**.

### Réception de marchandise

Quand la livraison arrive :

1. Allez dans **Cuisine → Réceptions**
2. Cliquez sur **Nouvelle réception**
3. Liez au bon de commande correspondant (si existant) ou créez une réception libre
4. Vérifiez les **quantités reçues** (peuvent différer de la commande)
5. Cliquez sur **Valider la réception**

Le stock des ingrédients est automatiquement mis à jour.

### Inventaire

Réalisez un inventaire pour corriger les écarts entre stock théorique et stock réel :

1. Allez dans **Cuisine → Stock → Inventaires**
2. Cliquez sur **Nouvel inventaire**
3. Pour chaque ingrédient, entrez la **quantité physiquement comptée**
4. Cliquez sur **Valider l'inventaire**

Le stock est mis à jour selon les quantités réelles comptées.

### Enregistrer une casse

Quand un produit est accidentellement abîmé ou périmé :

1. Allez dans **Cuisine → Stock → Casses**
2. Cliquez sur **Nouvelle casse**
3. Sélectionnez l'ingrédient, la quantité et le motif
4. Validez

Le stock est diminué en conséquence.

### Rapports de stock

Via **Cuisine → Stock → État à date** :
- Consultez le stock de tous les ingrédients à une date précise
- Exportez en **Excel** pour un rapport complet
- Imprimez l'état du stock

---

## 7. Serveuse / Serveur

### Interface Restaurant (TPE)

L'interface restaurant est conçue pour être rapide et simple. Elle s'ouvre automatiquement quand vous accédez au module **Restaurant**.

### Prendre une commande

1. **Sélectionnez une table** : les tables disponibles sont affichées. Une table occupée (en orange) a une commande en cours.
2. Si aucune commande n'est en cours sur cette table, elle est **créée automatiquement**.
3. **Ajoutez des plats** : naviguez dans les catégories du menu et cliquez sur le plat souhaité.
4. **Ajoutez des boissons** : passez à l'onglet Boissons pour sélectionner des articles de la cave.
5. **Ajoutez des accompagnements** : certains plats proposent des options (riz, frites, légumes...). Cliquez sur le plat dans la commande pour choisir l'accompagnement.
6. **Modifiez les quantités** : dans la commande en cours, utilisez + et - pour ajuster.

### Valider et encaisser

Une fois la commande terminée :

1. Cliquez sur **Valider la commande**
2. Choisissez le **mode de paiement** :
   - Espèces
   - Carte bancaire
   - Chambre (client hôtel — la facture est débitée sur sa chambre)
3. Cliquez sur **Confirmer l'encaissement**
4. Le ticket est généré automatiquement

### Annuler une commande

Si le client change d'avis avant encaissement :

1. Ouvrez la commande en cours
2. Cliquez sur **Annuler la commande**
3. Confirmez

Le stock des articles est automatiquement restitué.

### Réservations de table

Pour réserver une table pour un client :

1. Allez dans **Restaurant → Réservations**
2. Cliquez sur **Nouvelle réservation**
3. Remplissez : nom du client, nombre de personnes, date et heure, table souhaitée
4. Cliquez sur **Réserver**

> Le logiciel vérifie automatiquement qu'il n'y a pas de chevauchement avec une autre réservation sur la même table.

#### Gérer les statuts des réservations
- **En attente** → **Confirmée** → **Arrivée** → **Terminée**
- **Annulée** : si le client ne vient pas

---

## 8. Piscine & Espaces Événementiels

### Module Piscine

#### Enregistrer une entrée

1. Accédez au module **Piscine**
2. Cliquez sur **Nouvelle entrée**
3. Choisissez le type de visiteur :
   - **Visiteur ordinaire** (tarif adulte ou enfant)
   - **Résident hôtel** (tarif préférentiel)
   - **Forfait VIP** (package avec boissons et services)
4. Entrez le nom du visiteur
5. Cliquez sur **Enregistrer l'entrée**

#### Ajouter des consommations (piscine)

Pendant que le client est à la piscine :
1. Retrouvez son **accès actif** dans la liste
2. Cliquez sur **Ajouter une consommation**
3. Sélectionnez boisson ou plat, quantité
4. Cliquez sur **Ajouter**

#### Encaisser la sortie

Quand le client part :
1. Retrouvez son accès dans la liste
2. Cliquez sur **Encaisser la sortie**
3. Vérifiez le total (entrée + consommations)
4. Choisissez le mode de paiement
5. Confirmez — le ticket est généré

#### Configurer les tarifs

*Managers uniquement* — via **Piscine → Configurer les tarifs** :
- Tarif adulte visiteur / enfant visiteur
- Tarif adulte hébergé / enfant hébergé

### Module Espaces Événementiels

#### Voir les disponibilités

Le calendrier affiché sur la page d'accueil du module montre toutes les réservations en cours par espace et par date.

#### Créer une réservation d'espace

1. Accédez au module **Espaces**
2. Cliquez sur l'espace souhaité pour voir ses détails (capacité, équipements, tarif)
3. Cliquez sur **Réserver**
4. Remplissez :
   - Nom du client / entreprise
   - Date et heure de début / fin
   - Nombre de personnes
5. Le **prix est calculé automatiquement** selon la durée et le type de client (particulier, professionnel, résident hôtel)
6. Cliquez sur **Confirmer la réservation**

#### Encaisser une réservation d'espace

1. Retrouvez la réservation dans la liste
2. Cliquez sur **Encaisser**
3. Choisissez : paiement direct ou facturation sur chambre
4. Confirmez
5. Imprimez le **reçu** ou le **contrat** si demandé

#### Annuler une réservation

1. Retrouvez la réservation
2. Cliquez sur **Annuler**
3. Indiquez le motif d'annulation
4. Confirmez

---

## 9. Facturation

### Vue d'ensemble

Le module Facturation centralise tous les documents financiers : tickets, factures, proformas (devis) et avoirs.

### Tickets

Un ticket est généré automatiquement à chaque encaissement (restaurant, hôtel, piscine, cave...). Pour les consulter :

1. Allez dans **Facturation → Tickets**
2. Filtrez par date, module, montant
3. Cliquez sur un ticket pour voir le détail
4. Cliquez sur **Réimprimer** pour réimprimer
5. Cliquez sur **Exporter PDF** pour sauvegarder

### Créer une facture

Pour les clients professionnels ou les séjours nécessitant une facture officielle :

1. Allez dans **Facturation → Factures**
2. Cliquez sur **Nouvelle facture**
3. Sélectionnez le **client**
4. Ajoutez les **lignes de facturation** (services, nuitées, consommations)
5. Appliquez une **remise** si nécessaire
6. Cliquez sur **Créer la facture**
7. Exportez en **PDF** pour envoi

### Créer un devis (proforma)

Un devis est un document non définitif présentant une offre tarifaire :

1. Allez dans **Facturation → Proformas**
2. Cliquez sur **Nouveau proforma**
3. Remplissez comme une facture
4. Une fois accepté par le client, cliquez sur **Convertir en facture**

### Créer un avoir

Un avoir annule tout ou partie d'une facture (remboursement) :

1. Allez dans **Facturation → Avoirs** ou ouvrez le ticket concerné
2. Cliquez sur **Créer un avoir**
3. Indiquez le montant et le motif
4. Confirmez

---

## 10. Questions fréquentes

**Q : Je ne vois pas un module dans le menu — pourquoi ?**  
R : Votre compte n'a pas accès à ce module. Contactez votre Manager pour ajuster vos droits.

**Q : Le stock s'est décrémenté automatiquement — est-ce normal ?**  
R : Oui. Dès qu'une vente est validée (restaurant, piscine, hôtel), les articles correspondants sont automatiquement retirés du stock.

**Q : J'ai fait une erreur dans une commande déjà encaissée — que faire ?**  
R : Allez dans **Facturation** et créez un **Avoir** sur le ticket concerné. Contactez ensuite votre Manager pour les corrections de stock si nécessaire.

**Q : La caisse indique "une session est déjà ouverte" — que faire ?**  
R : Une session est peut-être restée ouverte depuis la veille. Le Chef caissier(e) ou le Manager peut forcer sa clôture depuis le module Caisse.

**Q : Un client veut payer sa note de restaurant sur sa chambre — comment faire ?**  
R : Lors de la validation de la commande, sélectionnez le mode de paiement **Chambre**, puis choisissez la chambre du client dans la liste.

**Q : Je ne peux pas me connecter — que faire ?**  
R : Vérifiez que vous utilisez le bon identifiant (pas votre email, mais votre identifiant de connexion). Si le problème persiste, contactez votre Manager pour une réinitialisation de mot de passe.

**Q : Comment savoir si la caisse est ouverte ou fermée ?**  
R : Le Dashboard affiche l'état de la caisse en permanence. Une caisse ouverte affiche son solde ; une caisse fermée affiche "Fermée".

**Q : Peut-on modifier le prix d'un article au moment de la vente ?**  
R : Non. Les prix sont définis dans le paramétrage par les managers. Si un prix est incorrect, signalez-le à votre Manager.

**Q : Comment imprimer un document ?**  
R : Chaque document (ticket, rapport, fiche, contrat) dispose d'un bouton **Imprimer** ou **Export PDF**. Cliquez dessus — la fenêtre d'impression de votre navigateur s'ouvre.

---

## Contacts et support

En cas de problème technique non résolu par ce manuel, contactez :

- **Votre Manager direct** pour les questions d'accès et de droits
- **Le Directeur Général** pour les problèmes de configuration
- **L'administrateur système** (accès `/admin/`) pour les problèmes techniques

---

*Manuel rédigé pour le Complexe Hôtelier Behanian — Usage interne uniquement*
