"""
Logique métier partagée pour la suppression d'un Ticket — utilisée à la fois
par la vue `ticket_delete` (bouton Facturation) et par `TicketAdmin` (Django
Admin), afin que TOUTE suppression d'un ticket restaure le stock et supprime
les transactions liées, quelle que soit l'interface utilisée.
"""
import re
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType

from .models import Ticket, Article, LignePaiement

_MODES_MOBILES = {'wave', 'orange_money', 'mtn_money', 'moov_money', 'mobile_money', 'mobile'}


def creer_lignes_paiement(ticket, lignes):
    """
    Crée les LignePaiement pour un ticket et met à jour les champs de
    rétrocompatibilité (mode_paiement, montant_especes) sur le ticket.

    lignes : list[dict] — ex. [{'mode':'wave','montant':2000},
                                {'mode':'especes','montant':2500}]
    Les lignes à montant ≤ 0 sont ignorées.
    Met à jour le ticket en base (update_fields limités pour ne pas écraser
    d'autres champs en cours de création).
    """
    lignes = [l for l in lignes if Decimal(str(l['montant'])) > 0]
    if not lignes:
        return

    LignePaiement.objects.filter(ticket=ticket).delete()
    for l in lignes:
        LignePaiement.objects.create(
            ticket=ticket,
            mode_paiement=l['mode'],
            montant=Decimal(str(l['montant'])),
        )

    # --- rétrocompatibilité sur Ticket ---
    modes_mobiles = [l['mode'] for l in lignes if l['mode'] in _MODES_MOBILES]
    montant_esp   = sum(Decimal(str(l['montant'])) for l in lignes if l['mode'] == 'especes')

    if len(lignes) == 1:
        mode_ticket = lignes[0]['mode']
        esp_ticket  = Decimal('0')
    elif len(modes_mobiles) == 1 and montant_esp > 0:
        # espèces + un mobile
        mode_ticket = modes_mobiles[0]
        esp_ticket  = montant_esp
    else:
        # multi-mobile OU autre combinaison complexe
        mode_ticket = 'mixte'
        esp_ticket  = montant_esp

    ticket.mode_paiement  = mode_ticket
    ticket.montant_especes = esp_ticket
    ticket.save(update_fields=['mode_paiement', 'montant_especes'])


def lignes_from_mode(mode, montant_total, montant_especes=0):
    """Construit une liste de lignes depuis l'ancien format (mode + espèces partiel).
    Utilisé pour les appels qui n'envoient pas encore lignes_paiement.
    """
    mt = Decimal(str(montant_total))
    me = Decimal(str(montant_especes or 0))
    if mode in _MODES_MOBILES and me > 0:
        return [
            {'mode': 'especes', 'montant': me},
            {'mode': mode,      'montant': max(Decimal('0'), mt - me)},
        ]
    return [{'mode': mode or 'especes', 'montant': mt}]


def aggregate_par_mode(ticket_qs):
    """
    Agrège les montants par mode de paiement pour un queryset de Tickets.
    Priorité aux LignePaiement quand elles existent (nouveaux tickets),
    fallback sur les champs Ticket.mode_paiement + montant_especes (anciens tickets).

    Retourne un dict {mode_paiement: montant_int}.
    Ex: {'especes': 15000, 'wave': 8000, 'orange_money': 5000}
    """
    from django.db.models import Sum as _Sum

    result = {}

    # ─── Tickets avec LignePaiement (nouveaux) ───
    ticket_ids_avec_lignes = set(
        LignePaiement.objects.filter(ticket__in=ticket_qs).values_list('ticket_id', flat=True)
    )
    if ticket_ids_avec_lignes:
        for row in (
            LignePaiement.objects
            .filter(ticket_id__in=ticket_ids_avec_lignes)
            .values('mode_paiement')
            .annotate(total=_Sum('montant'))
        ):
            mode = row['mode_paiement']
            result[mode] = result.get(mode, 0) + int(row['total'] or 0)

    # ─── Anciens tickets sans LignePaiement ───
    old_qs = ticket_qs.exclude(id__in=ticket_ids_avec_lignes)

    # Espèces pures
    s = int(old_qs.filter(mode_paiement='especes').aggregate(s=_Sum('montant_total'))['s'] or 0)
    if s:
        result['especes'] = result.get('especes', 0) + s

    # Mobile (± espèces)
    for mode in _MODES_MOBILES:
        r = old_qs.filter(mode_paiement=mode).aggregate(
            total=_Sum('montant_total'), esp=_Sum('montant_especes')
        )
        if r['total']:
            esp_part    = int(r['esp'] or 0)
            mobile_part = int(r['total']) - esp_part
            result['especes'] = result.get('especes', 0) + esp_part
            result[mode]      = result.get(mode, 0) + mobile_part

    # Autres modes
    for mode in ('carte_bancaire', 'carte', 'virement', 'cheque', 'autre'):
        s = int(old_qs.filter(mode_paiement=mode).aggregate(s=_Sum('montant_total'))['s'] or 0)
        if s:
            result[mode] = result.get(mode, 0) + s

    return result


def supprimer_ticket(ticket, user):
    """
    Restaure le stock des articles vendus (restaurant, hôtel, cave, piscine),
    supprime la transaction source correspondante (commande, réservation,
    vente, accès piscine) ainsi que les avoirs liés, puis supprime le ticket.

    Doit être appelée à l'intérieur d'une transaction atomique par l'appelant.
    Retourne (infos, avertissement) — deux éléments textuels pour informer
    l'utilisateur de ce qui a été fait / de ce qu'il faut vérifier manuellement.
    """
    numero = ticket.numero
    infos = []
    avertissement = ''

    if ticket.module == 'restaurant' and ticket.objet_id:
        from restaurant.models import Commande
        from cuisine.utils import process_stock_movement
        from bar.models import MouvementStockBar
        commande = Commande.objects.filter(id=ticket.objet_id).first()
        if commande:
            lignes = list(commande.lignes.select_related('plat', 'accompagnement', 'boisson').all())
            for ligne in lignes:
                process_stock_movement(
                    ligne.plat, ligne.quantite, 'entree', user,
                    f"Suppression Ticket {numero}"
                )
                if ligne.accompagnement:
                    process_stock_movement(
                        ligne.accompagnement, ligne.quantite, 'entree', user,
                        f"Suppression Ticket {numero}"
                    )
                if ligne.boisson:
                    MouvementStockBar.objects.create(
                        boisson=ligne.boisson, type_mouvement='entree', quantite=ligne.quantite,
                        commentaire=f"Suppression Ticket {numero}", utilisateur=user,
                    )
            if lignes:
                infos.append("le stock des articles a été restauré")
            table = commande.table
            commande.delete()
            if table:
                autres_actives = Commande.objects.filter(
                    table=table, statut__in=['en_attente', 'en_preparation', 'prete', 'servie']
                ).exists()
                if not autres_actives:
                    table.statut = 'disponible'
                    table.save(update_fields=['statut'])
        else:
            avertissement = "La commande d'origine est introuvable — aucun stock n'a été modifié."

    elif ticket.module == 'hotel' and ticket.objet_id:
        from hotel.models import Reservation
        from cuisine.utils import process_stock_movement
        from bar.models import BoissonBar
        from django.db.models import F
        reservation = Reservation.objects.filter(id=ticket.objet_id).first()
        if reservation:
            consos = list(reservation.consommations.all())
            for conso in consos:
                if conso.type_service == 'bar' and conso.boisson_id:
                    BoissonBar.objects.filter(pk=conso.boisson_id).update(
                        quantite_stock=F('quantite_stock') + conso.quantite
                    )
                elif conso.type_service == 'restaurant' and conso.plat_id:
                    process_stock_movement(
                        conso.plat, conso.quantite, 'entree', user,
                        f"Suppression Ticket {numero}"
                    )
            if consos:
                infos.append("le stock des consommations a été restauré")
                reservation.consommations.all().delete()
            if reservation.statut == 'terminee':
                reservation.statut = 'en_cours'
                reservation.save(update_fields=['statut'])
                if reservation.chambre and reservation.chambre.statut == 'disponible':
                    reservation.chambre.statut = 'occupee'
                    reservation.chambre.save(update_fields=['statut'])
                infos.append("le séjour a été remis en cours")
        else:
            avertissement = "La réservation d'origine est introuvable — aucun stock n'a été modifié."

    elif ticket.module == 'cave' and ticket.objet_id:
        from bar.models import VenteCave
        vente = VenteCave.objects.filter(id=ticket.objet_id).first()
        if vente:
            lignes_cave = list(vente.lignes.select_related('boisson').all())
            restaurees = 0
            for ligne in lignes_cave:
                if ligne.boisson:
                    ligne.boisson.restock(ligne.quantite, f"Suppression Ticket {numero}", user)
                    restaurees += 1
            if restaurees:
                infos.append("le stock des articles a été restauré")
            if len(lignes_cave) > restaurees:
                avertissement = (
                    "Certains articles de la vente n'ont pas pu être identifiés en stock "
                    "(article supprimé depuis) — vérifiez le stock manuellement."
                )
            vente.delete()
        else:
            avertissement = "La vente d'origine est introuvable — aucun stock n'a été modifié."

    elif ticket.module == 'piscine' and ticket.objet_id:
        from piscine.models import AccesPiscine
        from bar.models import BoissonBar, MouvementStockBar
        from restaurant.models import PlatMenu
        from cuisine.utils import process_stock_movement
        acces = AccesPiscine.objects.filter(id=ticket.objet_id).first()
        if acces:
            consos = list(acces.consommations.all())
            restaurees = 0
            for conso in consos:
                boisson = BoissonBar.objects.filter(nom=conso.produit).first()
                if boisson:
                    MouvementStockBar.objects.create(
                        boisson=boisson, type_mouvement='entree', quantite=conso.quantite,
                        commentaire=f"Suppression Ticket {numero}", utilisateur=user,
                    )
                    restaurees += 1
                    continue
                plat = PlatMenu.objects.filter(nom=conso.produit).first()
                if plat:
                    process_stock_movement(
                        plat, conso.quantite, 'entree', user,
                        f"Suppression Ticket {numero}"
                    )
                    restaurees += 1
            if restaurees:
                infos.append("le stock des articles a été restauré")
            acces.delete()
        else:
            avertissement = "L'accès piscine d'origine est introuvable — aucun stock n'a été modifié."

    elif ticket.module == 'espace' and ticket.objet_id:
        from espaces_evenementiels.models import ReservationEspace
        reservation_espace = ReservationEspace.objects.filter(id=ticket.objet_id).first()
        if reservation_espace:
            reservation_espace.delete()
            infos.append("la réservation d'espace a été supprimée")
        else:
            avertissement = "La réservation d'espace d'origine est introuvable."
    else:
        avertissement = (
            "Ce module ne permet pas de retrouver automatiquement les articles vendus : "
            "vérifiez et ajustez le stock manuellement si nécessaire."
        )

    nb_avoirs = ticket.avoirs.count()
    if nb_avoirs:
        ticket.avoirs.all().delete()
        infos.append(f"{nb_avoirs} avoir(s) lié(s) supprimé(s)")

    Article.objects.filter(
        content_type=ContentType.objects.get_for_model(Ticket),
        object_id=ticket.id,
    ).delete()

    ticket.delete()

    return infos, avertissement


def _parser_contenu_ticket(contenu):
    """Parse le contenu d'un ticket — retourne une liste de (designation, prix)."""
    if not contenu:
        return []
    lignes = []
    if '<div class="row">' in contenu or '<div class=' in contenu:
        noms = re.findall(r'<span[^>]*class=[^>]*item-name[^>]*>(.*?)</span>', contenu, re.DOTALL)
        prix_list = re.findall(r'<span[^>]*class=[^>]*item-price[^>]*>(.*?)</span>', contenu, re.DOTALL)
        for i, nom in enumerate(noms):
            nom_clean = re.sub(r'<[^>]+>', '', nom).strip()
            if not nom_clean:
                continue
            prix_val = Decimal('0')
            if i < len(prix_list):
                prix_str = re.sub(r'[^\d]', '', prix_list[i].replace(',', '').replace(' ', '').strip())
                try:
                    prix_val = Decimal(prix_str) if prix_str else Decimal('0')
                except Exception:
                    pass
            lignes.append((nom_clean, prix_val))
    else:
        for line in contenu.split('\n'):
            line = line.strip()
            if not line or line.startswith(('=', 'TOTAL', 'Reglement', 'Recu', 'Rendu',
                                            'COMPLEXE', 'Ticket', 'Date', 'Espace', 'Ref')):
                continue
            match = re.match(r'^(.+?)\s+([\d,\s]+)\s*F\s*$', line)
            if match:
                nom = match.group(1).strip()
                prix_str = match.group(2).replace(',', '').replace(' ', '').strip()
                try:
                    lignes.append((nom, Decimal(prix_str)))
                except Exception:
                    pass
    return lignes


def consolider_tickets_en_facture(ticket_ids, client_nom, client_telephone, user, notes=''):
    """
    Regroupe N tickets de modules différents (restaurant, cave, espace, hôtel…)
    en une seule Facture globale pour un client B2B.

    - Les lignes de chaque ticket sont parsées et ajoutées à la facture avec
      un préfixe [Module] pour garder la traçabilité.
    - Chaque ticket est marqué `facture_consolidee = facture` : il sera ensuite
      exclu des totaux CA dans les rapports caisse (évite le double-comptage).

    Retourne la Facture créée.
    Lève ValueError si aucun ticket valide n'est trouvé ou si un ticket est
    déjà consolidé dans une autre facture.
    """
    from .models import Facture, LigneFacture, Client, generate_facture_numero
    from django.utils import timezone as tz
    from datetime import timedelta

    tickets = list(Ticket.objects.filter(id__in=ticket_ids).select_related('client'))
    if not tickets:
        raise ValueError("Aucun ticket trouvé pour les identifiants fournis.")

    deja_consolidees = [t.numero for t in tickets if t.facture_consolidee_id]
    if deja_consolidees:
        raise ValueError(
            f"Les tickets {', '.join(deja_consolidees)} sont déjà regroupés dans une facture."
        )

    client_nom = client_nom.strip()
    if not client_nom:
        raise ValueError("Le nom du client est obligatoire.")

    client, _ = Client.objects.get_or_create(
        nom=client_nom,
        defaults={'telephone': client_telephone.strip() if client_telephone else ''},
    )
    if client_telephone and not client.telephone:
        client.telephone = client_telephone.strip()
        client.save(update_fields=['telephone'])

    total = sum(t.montant_total for t in tickets)

    today = tz.now().date()
    facture = Facture.objects.create(
        numero=generate_facture_numero(),
        client=client,
        date_facturation=today,
        date_echeance=today + timedelta(days=30),
        statut='envoyee',
        sous_total=total,
        remise=Decimal('0'),
        taux_tva=Decimal('0'),
        montant_tva=Decimal('0'),
        total=total,
        notes=(
            (notes + '\n' if notes else '')
            + f"Regroupement de {len(tickets)} ticket(s) : "
            + ', '.join(t.numero for t in tickets)
        ),
        cree_par=user,
    )

    for ticket in tickets:
        lignes_parsed = _parser_contenu_ticket(ticket.contenu)
        prefix = f"[{ticket.get_module_display()}]"
        if lignes_parsed:
            for designation, prix in lignes_parsed:
                LigneFacture.objects.create(
                    facture=facture,
                    designation=f"{prefix} {designation}",
                    quantite=1,
                    prix_unitaire=prix,
                )
        else:
            LigneFacture.objects.create(
                facture=facture,
                designation=f"{prefix} {ticket.numero}",
                quantite=1,
                prix_unitaire=ticket.montant_total,
            )
        ticket.facture_consolidee = facture
        ticket.save(update_fields=['facture_consolidee'])

    return facture
