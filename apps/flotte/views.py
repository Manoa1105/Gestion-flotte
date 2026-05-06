"""
=============================================================================
Vues de l'app "flotte"
=============================================================================
5 vues pour le CRUD complet des camions :
  - camion_liste     (R) : liste avec recherche et filtres HTMX
  - camion_detail    (R) : page de détail
  - camion_creer     (C) : formulaire de création
  - camion_modifier  (U) : formulaire d'édition
  - camion_supprimer (D) : confirmation et suppression

Convention de routage REST :
  GET  /camions/              -> liste
  GET  /camions/nouveau/      -> formulaire vide
  POST /camions/nouveau/      -> validation + création
  GET  /camions/<id>/         -> détail
  GET  /camions/<id>/modifier/-> formulaire pré-rempli
  POST /camions/<id>/modifier/-> validation + mise à jour
  POST /camions/<id>/supprimer/-> suppression effective
=============================================================================
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Camion, Chauffeur
from .forms import CamionForm, ChauffeurForm


# =============================================================================
# CAMION : LISTE (avec recherche et filtres HTMX)
# =============================================================================
def camion_liste(request):
    """
    Liste des camions avec :
      - recherche textuelle (immatriculation, marque, modèle)
      - filtre par statut (chips cliquables)
      - pagination

    Particularité HTMX : si la requête vient d'HTMX (header HX-Request),
    on renvoie uniquement le partial HTML de la liste (pas la page entière).
    Cela permet de mettre à jour seulement la zone des résultats
    sans recharger la page.
    """

    # ---- Récupération des paramètres GET de filtrage ----
    # request.GET est un dict-like des paramètres dans l'URL (?recherche=xxx&statut=yyy)
    recherche = request.GET.get("recherche", "").strip()
    statut = request.GET.get("statut", "").strip()

    # ---- Construction du queryset (la requête SQL avant exécution) ----
    # On part de TOUS les camions, puis on filtre selon les paramètres reçus.
    camions = Camion.objects.all().order_by("immatriculation")

    # Filtre par texte (sur immatriculation OU marque OU modèle)
    if recherche:
        # Q permet de combiner plusieurs filtres avec des OU logiques
        camions = camions.filter(
            Q(immatriculation__icontains=recherche)
            | Q(marque__icontains=recherche)
            | Q(modele__icontains=recherche)
        )

    # Filtre par statut
    if statut:
        camions = camions.filter(statut=statut)

    # ---- Pagination (20 par page) ----
    paginator = Paginator(camions, 20)
    numero_page = request.GET.get("page", 1)
    page = paginator.get_page(numero_page)

    contexte = {
        "titre_page": "Camions",
        "page": page,
        "camions": page.object_list,
        "recherche": recherche,
        "statut_actif": statut,
        # On passe aussi la liste des statuts disponibles pour les chips
        "statuts": Camion.Statut.choices,
        # Stats rapides en haut de page
        "total_camions": Camion.objects.count(),
    }

    # ---- Détection HTMX ----
    # HTMX ajoute le header "HX-Request: true" sur ses requêtes.
    # Si la requête vient d'HTMX, on ne renvoie que le partial des résultats
    # (pour swap dans la div #liste-camions).
    if request.headers.get("HX-Request"):
        return render(request, "flotte/_camion_liste_resultats.html", contexte)

    return render(request, "flotte/camion_liste.html", contexte)


# =============================================================================
# CAMION : DÉTAIL
# =============================================================================
def camion_detail(request, pk):
    """
    Page de détail d'un camion.

    pk = primary key (ID du camion en base).
    get_object_or_404 : tente de récupérer le camion ; si l'ID n'existe pas,
    Django renvoie une page 404 propre au lieu de planter.
    """
    camion = get_object_or_404(Camion, pk=pk)

    # On récupère aussi les missions liées à ce camion (utile pour l'historique)
    missions = camion.missions.select_related(
        "ville_depart", "ville_arrivee", "chauffeur"
    ).order_by("-date_creation")[:10]

    contexte = {
        "titre_page": camion.description_courte,
        "camion": camion,
        "missions": missions,
    }
    return render(request, "flotte/camion_detail.html", contexte)


# =============================================================================
# CAMION : CRÉATION
# =============================================================================
def camion_creer(request):
    """
    Création d'un nouveau camion.

    GET  : on affiche un formulaire vide.
    POST : on valide les données ; si OK on sauve et on redirige vers le détail.
    """
    if request.method == "POST":
        # On instancie le formulaire avec les données reçues
        form = CamionForm(request.POST, request.FILES)
        if form.is_valid():
            camion = form.save()
            # Message flash affiché à la prochaine page
            messages.success(
                request,
                f"Le camion {camion.immatriculation} a été créé avec succès."
            )
            # Redirection vers la page de détail du camion créé
            return redirect("flotte:camion_detail", pk=camion.pk)
        # Si form.is_valid() est False, on retombe sur le render avec form.errors
    else:
        # GET : formulaire vide
        form = CamionForm()

    contexte = {
        "titre_page": "Nouveau camion",
        "form": form,
        "mode": "creation",
    }
    return render(request, "flotte/camion_form.html", contexte)


# =============================================================================
# CAMION : MODIFICATION
# =============================================================================
def camion_modifier(request, pk):
    """
    Modification d'un camion existant.
    Très similaire à camion_creer, sauf qu'on charge l'objet existant
    et qu'on passe instance=camion au formulaire.
    """
    camion = get_object_or_404(Camion, pk=pk)

    if request.method == "POST":
        # instance=camion : Django met à jour cet objet au lieu d'en créer un nouveau
        form = CamionForm(request.POST, request.FILES, instance=camion)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Le camion {camion.immatriculation} a été modifié."
            )
            return redirect("flotte:camion_detail", pk=camion.pk)
    else:
        # GET : formulaire pré-rempli avec les valeurs actuelles
        form = CamionForm(instance=camion)

    contexte = {
        "titre_page": f"Modifier {camion.immatriculation}",
        "form": form,
        "camion": camion,
        "mode": "modification",
    }
    return render(request, "flotte/camion_form.html", contexte)


# =============================================================================
# CAMION : SUPPRESSION
# =============================================================================
def camion_supprimer(request, pk):
    """
    Suppression d'un camion.

    GET  : page de confirmation (sécurité, pour éviter une suppression accidentelle).
    POST : suppression effective puis redirection vers la liste.

    Sécurité Django : la suppression DOIT passer par POST, pas par GET.
    Sinon n'importe quel lien (même un crawler Google) pourrait supprimer.
    """
    camion = get_object_or_404(Camion, pk=pk)

    if request.method == "POST":
        immat = camion.immatriculation
        try:
            camion.delete()
            messages.success(request, f"Le camion {immat} a été supprimé.")
            return redirect("flotte:camion_liste")
        except Exception as e:
            # Si le camion a des missions liées avec on_delete=PROTECT, ça plantera ici.
            messages.error(
                request,
                f"Impossible de supprimer ce camion : {e}. "
                f"Il a probablement des missions liées."
            )
            return redirect("flotte:camion_detail", pk=camion.pk)

    # GET : on affiche la page de confirmation
    contexte = {
        "titre_page": f"Supprimer {camion.immatriculation}",
        "camion": camion,
        # On compte les missions liées pour informer l'utilisateur
        "nb_missions": camion.missions.count(),
    }
    return render(request, "flotte/camion_confirmer_suppression.html", contexte)


# =============================================================================
# =============================================================================
# CHAUFFEURS - 5 VUES (même pattern que les camions)
# =============================================================================
# =============================================================================


# =============================================================================
# CHAUFFEUR : LISTE (avec recherche et filtres HTMX)
# =============================================================================
def chauffeur_liste(request):
    """Liste des chauffeurs avec recherche, filtre par statut, pagination, HTMX."""
    recherche = request.GET.get("recherche", "").strip()
    statut = request.GET.get("statut", "").strip()

    chauffeurs = Chauffeur.objects.all().order_by("nom", "prenom")

    if recherche:
        chauffeurs = chauffeurs.filter(
            Q(nom__icontains=recherche)
            | Q(prenom__icontains=recherche)
            | Q(numero_permis__icontains=recherche)
            | Q(telephone__icontains=recherche)
        )

    if statut:
        chauffeurs = chauffeurs.filter(statut=statut)

    paginator = Paginator(chauffeurs, 20)
    numero_page = request.GET.get("page", 1)
    page = paginator.get_page(numero_page)

    contexte = {
        "titre_page": "Chauffeurs",
        "page": page,
        "chauffeurs": page.object_list,
        "recherche": recherche,
        "statut_actif": statut,
        "statuts": Chauffeur.Statut.choices,
        "total_chauffeurs": Chauffeur.objects.count(),
    }

    # Détection HTMX : on renvoie juste le partial des résultats si oui
    if request.headers.get("HX-Request"):
        return render(request, "flotte/_chauffeur_liste_resultats.html", contexte)

    return render(request, "flotte/chauffeur_liste.html", contexte)


# =============================================================================
# CHAUFFEUR : DÉTAIL
# =============================================================================
def chauffeur_detail(request, pk):
    """Page de détail d'un chauffeur."""
    chauffeur = get_object_or_404(Chauffeur, pk=pk)

    # Missions récentes assurées par ce chauffeur
    missions = chauffeur.missions.select_related(
        "camion", "ville_depart", "ville_arrivee"
    ).order_by("-date_creation")[:10]

    contexte = {
        "titre_page": chauffeur.nom_complet,
        "chauffeur": chauffeur,
        "missions": missions,
    }
    return render(request, "flotte/chauffeur_detail.html", contexte)


# =============================================================================
# CHAUFFEUR : CRÉATION
# =============================================================================
def chauffeur_creer(request):
    """Création d'un nouveau chauffeur."""
    if request.method == "POST":
        form = ChauffeurForm(request.POST)
        if form.is_valid():
            chauffeur = form.save()
            messages.success(
                request,
                f"Le chauffeur {chauffeur.nom_complet} a été créé avec succès."
            )
            return redirect("flotte:chauffeur_detail", pk=chauffeur.pk)
    else:
        form = ChauffeurForm()

    contexte = {
        "titre_page": "Nouveau chauffeur",
        "form": form,
        "mode": "creation",
    }
    return render(request, "flotte/chauffeur_form.html", contexte)


# =============================================================================
# CHAUFFEUR : MODIFICATION
# =============================================================================
def chauffeur_modifier(request, pk):
    """Modification d'un chauffeur existant."""
    chauffeur = get_object_or_404(Chauffeur, pk=pk)

    if request.method == "POST":
        form = ChauffeurForm(request.POST, instance=chauffeur)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Le chauffeur {chauffeur.nom_complet} a été modifié."
            )
            return redirect("flotte:chauffeur_detail", pk=chauffeur.pk)
    else:
        form = ChauffeurForm(instance=chauffeur)

    contexte = {
        "titre_page": f"Modifier {chauffeur.nom_complet}",
        "form": form,
        "chauffeur": chauffeur,
        "mode": "modification",
    }
    return render(request, "flotte/chauffeur_form.html", contexte)


# =============================================================================
# CHAUFFEUR : SUPPRESSION
# =============================================================================
def chauffeur_supprimer(request, pk):
    """Suppression d'un chauffeur (avec page de confirmation)."""
    chauffeur = get_object_or_404(Chauffeur, pk=pk)

    if request.method == "POST":
        nom = chauffeur.nom_complet
        try:
            chauffeur.delete()
            messages.success(request, f"Le chauffeur {nom} a été supprimé.")
            return redirect("flotte:chauffeur_liste")
        except Exception as e:
            messages.error(
                request,
                f"Impossible de supprimer ce chauffeur : {e}. "
                f"Il a probablement des missions liées."
            )
            return redirect("flotte:chauffeur_detail", pk=chauffeur.pk)

    contexte = {
        "titre_page": f"Supprimer {chauffeur.nom_complet}",
        "chauffeur": chauffeur,
        "nb_missions": chauffeur.missions.count(),
    }
    return render(request, "flotte/chauffeur_confirmer_suppression.html", contexte)
