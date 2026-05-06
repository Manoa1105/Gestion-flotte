"""
=============================================================================
Processeur de contexte — app comptes
=============================================================================
Un context processor est une fonction appelée automatiquement par Django
pour CHAQUE requête. Elle renvoie un dict dont les clés deviennent des
variables disponibles dans TOUS les templates, sans qu'on ait besoin de
les passer manuellement depuis chaque vue.

On l'enregistre dans settings.py > TEMPLATES > context_processors.

Ici, on injecte le rôle de l'utilisateur connecté pour que base.html
puisse afficher ou masquer les liens de navigation selon le rôle.
=============================================================================
"""


def role_courant(request):
    """
    Injecte {{ profil_role }} dans tous les templates.

    Valeurs possibles :
      "GESTIONNAIRE"  → accès complet
      "COMPTABLE"     → finances + missions (lecture)
      "CHAUFFEUR"     → ses propres missions
      ""              → utilisateur non connecté
    """
    if not request.user.is_authenticated:
        return {"profil_role": ""}

    # Les superusers ont les mêmes droits qu'un gestionnaire
    if request.user.is_superuser:
        return {"profil_role": "GESTIONNAIRE"}

    try:
        return {"profil_role": request.user.profil.role}
    except AttributeError:
        # Utilisateur sans profil (ne devrait pas arriver en prod)
        return {"profil_role": ""}
