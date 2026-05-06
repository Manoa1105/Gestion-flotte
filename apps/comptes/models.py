"""
=============================================================================
Modèles de l'app comptes
=============================================================================
On ne crée PAS un modèle User personnalisé (ça complique les migrations).
À la place, on utilise une relation 1-to-1 : chaque User Django a exactement
un ProfilUtilisateur qui lui attribue un rôle métier.

C'est le pattern "User profile" recommandé par Django.
=============================================================================
"""
from django.contrib.auth.models import User
from django.db import models


class ProfilUtilisateur(models.Model):
    """
    Extension du compte Django avec un rôle métier.

    Trois rôles disponibles :
      GESTIONNAIRE → accès complet (toutes les sections + gestion des users)
      COMPTABLE    → dashboard + finances (lecture + écriture) + missions (lecture)
      CHAUFFEUR    → tableau de bord + ses propres missions uniquement
    """

    class Role(models.TextChoices):
        GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire"
        COMPTABLE    = "COMPTABLE",    "Comptable"
        CHAUFFEUR    = "CHAUFFEUR",    "Chauffeur"

    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profil",
        verbose_name="compte utilisateur",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.GESTIONNAIRE,
        verbose_name="rôle",
    )
    # Lien optionnel : si le compte est de type CHAUFFEUR, on peut le relier
    # à un enregistrement Chauffeur de l'app flotte. Cela permet de filtrer
    # automatiquement les missions visibles (seulement les siennes).
    chauffeur_lie = models.OneToOneField(
        "flotte.Chauffeur",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="compte_utilisateur",
        verbose_name="chauffeur associé",
    )

    class Meta:
        verbose_name = "profil utilisateur"
        verbose_name_plural = "profils utilisateurs"
        ordering = ["utilisateur__username"]

    def __str__(self):
        return f"{self.utilisateur.username} ({self.get_role_display()})"

    @property
    def nom_affichage(self):
        """Prénom + nom si renseignés, sinon le username."""
        u = self.utilisateur
        if u.first_name or u.last_name:
            return f"{u.first_name} {u.last_name}".strip()
        return u.username

    @property
    def est_gestionnaire(self):
        return self.role == self.Role.GESTIONNAIRE

    @property
    def est_comptable(self):
        return self.role == self.Role.COMPTABLE

    @property
    def est_chauffeur(self):
        return self.role == self.Role.CHAUFFEUR
