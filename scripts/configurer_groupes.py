
from django.contrib.auth.models import Group, Permission, User

def get_p(app, codes):
    result = []
    for c in codes:
        try:
            result.append(Permission.objects.get(content_type__app_label=app, codename=c))
        except Permission.DoesNotExist:
            pass
    return result

def cfg(nom, perms):
    g, _ = Group.objects.get_or_create(name=nom)
    g.permissions.set(perms)
    print(nom + " : " + str(g.permissions.count()) + " permissions")
    return g

# INTOUCHABLES
INTOUCHABLES = ["delete_ticket","delete_facture","delete_avoir","delete_ligneavoir","delete_lignefacture","delete_proforma","delete_ligneproforma","delete_caissesession","delete_mouvementstock","delete_mouvementstockcuisine","delete_mouvementstockbar","delete_logentry","delete_permission","delete_group"]

# 1. Manager General
mg = []
for app in ["bar","restaurant","hotel","cuisine","piscine","boite_nuit","espaces_evenementiels","caisse","facturation","parametres"]:
    [mg.append(p) for p in Permission.objects.filter(content_type__app_label=app) if p.codename not in INTOUCHABLES]
[mg.append(p) for p in Permission.objects.filter(content_type__app_label="auth") if p.codename not in INTOUCHABLES]
cfg("Manager General(e)", mg)

# 2. Manager Cuisine
mc = [p for p in Permission.objects.filter(content_type__app_label="cuisine") if p.codename not in ["delete_bonreception","delete_bonreceptioncuisine","delete_lignebonreception","delete_lignebonreceptioncuisine","delete_mouvementstock","delete_mouvementstockcuisine"]]
mc += get_p("restaurant", ["view_platmenu","view_categoriemenu"])
mc += get_p("facturation", ["view_ticket","view_facture"])
cfg("Manager Cuisine", mc)

# 3. Receptionniste
rcp = [p for p in Permission.objects.filter(content_type__app_label="hotel") if p.codename not in ["delete_chambre","delete_client"]]
rcp += get_p("facturation", ["add_ticket","change_ticket","view_ticket","add_client","change_client","view_client","view_facture"])
rcp += get_p("bar", ["view_boissonbar","view_categoriebar"])
rcp += get_p("restaurant", ["view_platmenu","view_categoriemenu"])
rcp += get_p("espaces_evenementiels", ["view_espaceevenementiel"])
rcp += get_p("auth", ["view_user","view_group"])
cfg("Receptionniste", rcp)

# 4. Caissier/Caissiere
cs = get_p("restaurant", ["add_commande","change_commande","view_commande","add_lignecommande","change_lignecommande","view_lignecommande","view_table","view_platmenu","view_categoriemenu"])
cs += get_p("bar", ["view_boissonbar","view_categoriebar","view_tablebar","add_mouvementstockbar","view_mouvementstockbar"])
cs += [p for p in Permission.objects.filter(content_type__app_label="piscine") if "delete" not in p.codename]
cs += [p for p in Permission.objects.filter(content_type__app_label="espaces_evenementiels") if "delete" not in p.codename]
cs += get_p("facturation", ["add_ticket","change_ticket","view_ticket","add_client","view_client"])
cs += get_p("auth", ["view_user","view_group"])
cfg("Caissiere / Caissier", cs)

# 5. Caissier Principal
cp = get_p("caisse", ["add_caissesession","change_caissesession","view_caissesession"])
cp += get_p("facturation", ["view_ticket","view_facture","add_ticket","change_ticket","add_client","view_client"])
cp += get_p("auth", ["view_user","view_group"])
for app in ["hotel","restaurant","bar","piscine","espaces_evenementiels"]:
    cp += list(Permission.objects.filter(content_type__app_label=app, codename__startswith="view_"))
cfg("Caissier(ere) Principal(e)", cp)

# 6. Serveur
cfg("Serveuse/Serveur", [])

# Retirer is_staff
for u in User.objects.filter(is_superuser=False, is_staff=True):
    u.is_staff = False
    u.save()
    print(u.username + " : is_staff -> False")

print("TERMINE")
