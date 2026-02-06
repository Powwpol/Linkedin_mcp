"""Engagement optimizer skill for LinkedIn posts.

This skill focuses on maximizing algorithmic and human engagement signals:
- Hook optimization (scroll-stopping first lines)
- Readability scoring and line structure
- CTA selection based on objective
- Hashtag strategy (reach vs niche balance)
- Optimal posting patterns
- Comment-bait techniques (ethical)

Based on analysis of high-performing LinkedIn posts and
the LinkedIn algorithm's known ranking signals.
"""

from __future__ import annotations

from linkedin_mcp.skills.business_context import BusinessContext


class EngagementSkill:
    """Generates prompts focused on maximizing LinkedIn post engagement."""

    # LinkedIn algorithm ranking signals (documented + observed)
    ALGORITHM_SIGNALS = {
        "dwell_time": (
            "Temps de lecture : LinkedIn mesure combien de temps un utilisateur "
            "s'arrete sur votre post. Posts plus longs (>1200 chars) avec un "
            "bon espacement performent mieux car le dwell time est plus eleve."
        ),
        "early_engagement": (
            "Engagement precoce : Les 60 premieres minutes sont critiques. "
            "Les likes/commentaires dans cette fenetre determinent la portee "
            "organique. Poster quand votre audience est active."
        ),
        "meaningful_comments": (
            "Commentaires substantiels : LinkedIn valorise les commentaires "
            "de >12 mots vs les simples emojis. Poser des questions ouvertes "
            "qui necessitent des reponses elaborees."
        ),
        "creator_replies": (
            "Reponses du createur : Repondre aux commentaires dans les 30-60 min "
            "booste significativement la portee. Chaque reponse relance la "
            "distribution du post dans le feed."
        ),
        "saves_shares": (
            "Sauvegardes et partages : Signaux les plus puissants. "
            "Contenu 'sauvegardable' = listes, frameworks, templates. "
            "Contenu 'partageable' = insights originaux, donnees exclusives."
        ),
        "no_external_links": (
            "Pas de liens externes dans le post : LinkedIn penalise les posts "
            "avec des liens sortants (baisse de ~40% de portee). "
            "Placer le lien en commentaire ou utiliser 'lien en bio'."
        ),
    }

    # Hook formulas rated by effectiveness
    HOOK_FORMULAS = [
        {
            "name": "Le Chiffre Choc",
            "formula": "[Chiffre surprenant] + [consequence inattendue]",
            "example": "97% des posts LinkedIn sont ignores. Voici les 3% qui explosent.",
            "effectiveness": "Tres haute",
            "best_for": ["educate", "authority"],
        },
        {
            "name": "L'Anti-Conseil",
            "formula": "Arretez de [conseil courant]. [Raison contre-intuitive].",
            "example": "Arretez de publier tous les jours sur LinkedIn. Votre audience vous deteste.",
            "effectiveness": "Tres haute",
            "best_for": ["provoke", "contrarian"],
        },
        {
            "name": "La Confession",
            "formula": "J'ai [erreur/echec]. [Ce que j'ai appris].",
            "example": "J'ai perdu mon plus gros client la semaine derniere. Et c'est la meilleure chose qui me soit arrivee.",
            "effectiveness": "Haute",
            "best_for": ["story", "connect"],
        },
        {
            "name": "La Question Impossible",
            "formula": "[Question qui semble avoir une reponse evidente] + [twist]",
            "example": "Pourquoi les meilleurs vendeurs ne vendent jamais ?",
            "effectiveness": "Haute",
            "best_for": ["curiosity", "question"],
        },
        {
            "name": "Le Comparatif Violent",
            "formula": "[Annee/epoque] : [X]. [Annee actuelle] : [Y]. [Observation].",
            "example": "2020 : 10 candidatures pour 1 poste. 2024 : 300. Le marche a change. Pas votre strategie.",
            "effectiveness": "Haute",
            "best_for": ["data", "provoke"],
        },
        {
            "name": "L'Enumeration Promise",
            "formula": "[N] [choses] que [segment] [resultat]. (Surtout le #[N]).",
            "example": "7 erreurs qui tuent votre taux de conversion. (Surtout la #5).",
            "effectiveness": "Moyenne-Haute",
            "best_for": ["list", "educate"],
        },
        {
            "name": "Le Dialogue Direct",
            "formula": "Citation verbatim + contexte minimum",
            "example": "'On n'a pas le budget.' — Mon client, 2 jours avant de signer un contrat a 50K.",
            "effectiveness": "Haute",
            "best_for": ["story", "sales"],
        },
        {
            "name": "L'Observation Silencieuse",
            "formula": "Personne ne parle de [X]. [Raison pour laquelle c'est important].",
            "example": "Personne ne parle du vrai cout du remote : l'isolement strategique.",
            "effectiveness": "Moyenne-Haute",
            "best_for": ["thought_leadership", "contrarian"],
        },
    ]

    # CTA strategies by objective
    CTA_STRATEGIES = {
        "comments": {
            "description": "Maximiser les commentaires (meilleur signal algo)",
            "techniques": [
                "Poser un dilemme a 2 options : 'Team [A] ou Team [B] ?'",
                "Demander de completer : 'Le meilleur conseil qu'on m'a donne : ___'",
                "Inviter le desaccord : 'Changez-moi d'avis en commentaire'",
                "Demander un temoignage : 'Racontez votre experience avec [X]'",
                "Creer un debat : 'D'accord ou pas d'accord ?'",
            ],
        },
        "saves": {
            "description": "Maximiser les sauvegardes (contenu reference)",
            "techniques": [
                "Donner un framework complet et actionnable",
                "Creer une checklist qu'on peut reappliquer",
                "Partager une liste de ressources curatives",
                "Finir par : 'Sauvegardez ce post pour y revenir'",
                "Utiliser des listes numerotees bien structurees",
            ],
        },
        "leads": {
            "description": "Generer des leads qualifies",
            "techniques": [
                "Offrir un lead magnet : 'Commentez [MOT] et je vous envoie [X]'",
                "Proposer un audit gratuit : 'DM moi [MOT] pour un diagnostic offert'",
                "Rediriger vers un lien bio : 'Le lien est dans mon profil'",
                "Inviter a un appel : 'Reservez un slot dans mon Calendly (lien en commentaire)'",
                "Segmenter : 'Si vous etes [cible], DM moi'",
            ],
        },
        "shares": {
            "description": "Maximiser les partages (viralite)",
            "techniques": [
                "Creer un contenu identitaire ('Partagez si vous pensez aussi que...')",
                "Donner une stat choquante facilement relayable",
                "Creer un format visuel/textuel memorable",
                "Formuler un contenu qui fait bien paraitre celui qui partage",
                "Faire un take audacieux que les gens veulent amplifier",
            ],
        },
        "profile_visits": {
            "description": "Maximiser les visites de profil",
            "techniques": [
                "Teaser une expertise rare sans tout reveler",
                "Mentionner un resultat impressionnant lie a votre activite",
                "Utiliser 'Plus de details dans mon profil'",
                "Creer un mystere sur qui vous etes/ce que vous faites",
                "Partager un succes client sans nommer le client",
            ],
        },
    }

    # Optimal posting schedule (based on aggregate data)
    POSTING_SCHEDULE = {
        "best_days": "Mardi, Mercredi, Jeudi",
        "best_times": "7h30-8h30, 12h00-13h00, 17h30-18h30 (heure locale de l'audience)",
        "worst_times": "Vendredi apres-midi, Weekend, Lundi matin avant 9h",
        "frequency": "3-5 posts/semaine pour la croissance, 2-3 pour le maintien",
        "spacing": "Minimum 18-24h entre deux posts (laisser l'algo distribuer)",
    }

    def __init__(self, context: BusinessContext):
        self.context = context

    def generate_engagement_prompt(
        self,
        topic: str,
        objective: str = "comments",
        hook_style: str | None = None,
    ) -> str:
        """Generate a prompt optimized for a specific engagement metric.

        Args:
            topic: The post subject.
            objective: Engagement goal (comments, saves, leads, shares, profile_visits).
            hook_style: Optional specific hook formula name, or auto-select.
        """
        cta_data = self.CTA_STRATEGIES.get(objective, self.CTA_STRATEGIES["comments"])
        context_block = self.context.to_prompt_block()

        hook_section = self._build_hook_section(hook_style)

        return f"""Tu es un expert en optimisation d'engagement LinkedIn.
Ta mission : creer un post sur **{topic}** qui maximise les **{cta_data['description']}**.

{context_block}

---

## Signaux algorithmiques LinkedIn a exploiter

{chr(10).join(f'- **{k}** : {v}' for k, v in self.ALGORITHM_SIGNALS.items())}

---

## Hook du post

{hook_section}

---

## Strategie CTA : {cta_data['description']}

Techniques a appliquer :
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(cta_data['techniques']))}

---

## Regles de structure pour l'engagement

1. **Longueur optimale** : 1200-1500 caracteres (sweet spot dwell time)
2. **Espacement** : Sauter une ligne entre chaque phrase/idee
   (maximise le scroll depth et le dwell time)
3. **Pas de lien externe** dans le corps du post
4. **3-5 hashtags** en fin de post
5. **Premier commentaire** : Preparer un commentaire du createur
   a poster immediatement apres publication (boost algo)

## Planning optimal

- {self.POSTING_SCHEDULE['best_days']}
- {self.POSTING_SCHEDULE['best_times']}
- {self.POSTING_SCHEDULE['frequency']}

---

Genere :
1. Le post complet (pret a publier)
2. Le premier commentaire a poster sous le post
3. 3 reponses-types pour les commentaires attendus
"""

    def get_hook_catalog(self) -> str:
        """Return the full hook formula catalog."""
        lines = ["# Catalogue des formules de hooks LinkedIn\n"]
        for h in self.HOOK_FORMULAS:
            lines.append(f"## {h['name']}")
            lines.append(f"**Formule** : {h['formula']}")
            lines.append(f"**Exemple** : {h['example']}")
            lines.append(f"**Efficacite** : {h['effectiveness']}")
            lines.append(f"**Ideal pour** : {', '.join(h['best_for'])}")
            lines.append("")
        return "\n".join(lines)

    def get_cta_catalog(self) -> str:
        """Return the CTA strategies catalog."""
        lines = ["# Catalogue des strategies CTA LinkedIn\n"]
        for key, data in self.CTA_STRATEGIES.items():
            lines.append(f"## `{key}` - {data['description']}")
            for t in data["techniques"]:
                lines.append(f"  - {t}")
            lines.append("")
        return "\n".join(lines)

    def _build_hook_section(self, hook_style: str | None) -> str:
        """Build the hook instruction section."""
        if hook_style:
            for h in self.HOOK_FORMULAS:
                if h["name"].lower() == hook_style.lower() or hook_style.lower() in h["name"].lower():
                    return (
                        f"Utilise la formule de hook **{h['name']}** :\n"
                        f"- Formule : {h['formula']}\n"
                        f"- Exemple : {h['example']}"
                    )

        lines = ["Choisis le hook le plus adapte au sujet parmi ces formules :\n"]
        for h in self.HOOK_FORMULAS[:4]:  # Top 4
            lines.append(f"- **{h['name']}** : {h['formula']}")
        return "\n".join(lines)
