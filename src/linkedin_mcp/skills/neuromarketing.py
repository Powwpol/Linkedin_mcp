"""Neuro-marketing skill for LinkedIn content creation.

This skill applies neuroscience-backed persuasion principles to
LinkedIn post creation. It generates prompts that guide the AI agent
to write posts leveraging cognitive biases, emotional triggers, and
attention-capture patterns proven to increase engagement.

Core neuro-marketing principles applied:
- Pattern interrupt (scroll-stopping hooks)
- Loss aversion & FOMO
- Social proof & authority bias
- Curiosity gap & information gap theory
- Reciprocity & value-first
- Anchoring & contrast effect
- Peak-end rule (memorable closings)
- Zeigarnik effect (open loops)
"""

from __future__ import annotations

from linkedin_mcp.skills.business_context import BusinessContext


class NeuroMarketingSkill:
    """Generates neuro-marketing-optimized prompts for LinkedIn posts."""

    # --- Cognitive bias templates ---
    # Each template describes a bias, when to use it, and a structural formula.

    COGNITIVE_BIASES = {
        "loss_aversion": {
            "name": "Aversion a la perte",
            "principle": (
                "Les gens ressentent la douleur d'une perte 2x plus fort que "
                "le plaisir d'un gain equivalent. Formuler le message en termes "
                "de ce que le lecteur PERD en n'agissant pas."
            ),
            "formula": (
                "1. Decrire ce que le lecteur perd (temps, argent, opportunite)\n"
                "2. Quantifier la perte si possible\n"
                "3. Montrer que la solution est accessible\n"
                "4. CTA qui elimine le risque"
            ),
            "hook_examples": [
                "Chaque jour sans [X], vous perdez [Y].",
                "J'ai perdu [X] avant de comprendre [Y].",
                "90% des [cible] font cette erreur qui leur coute [montant].",
            ],
        },
        "social_proof": {
            "name": "Preuve sociale",
            "principle": (
                "En situation d'incertitude, les gens suivent le comportement "
                "de la majorite. Montrer que d'autres personnes credibles "
                "ont deja adopte le comportement souhaite."
            ),
            "formula": (
                "1. Chiffre ou temoignage concret (noms, resultats)\n"
                "2. Montrer le mouvement/tendance ('de plus en plus de...')\n"
                "3. Inclure le lecteur dans le groupe ('comme vous, ils...')\n"
                "4. CTA pour rejoindre le mouvement"
            ),
            "hook_examples": [
                "[X] entreprises ont deja adopte [Y]. Et vous ?",
                "Quand j'ai vu [personne connue] faire [X], j'ai compris [Y].",
                "[Chiffre] professionnels utilisent deja [methode]. Voici pourquoi.",
            ],
        },
        "curiosity_gap": {
            "name": "Deficit de curiosite",
            "principle": (
                "Le cerveau ne supporte pas les boucles ouvertes. Creer un "
                "ecart entre ce que le lecteur sait et ce qu'il veut savoir "
                "force l'engagement (clic, lecture, commentaire)."
            ),
            "formula": (
                "1. Promettre une revelation ou un insight contre-intuitif\n"
                "2. Donner juste assez d'info pour amorcer la curiosite\n"
                "3. Retarder la reponse (la placer en milieu/fin de post)\n"
                "4. La revelation doit etre a la hauteur de la promesse"
            ),
            "hook_examples": [
                "Le secret que personne ne vous dit sur [sujet].",
                "J'ai decouvert [X] par accident. Ca a tout change.",
                "Il y a une raison pour laquelle [resultat surprenant]. Ce n'est pas celle que vous croyez.",
            ],
        },
        "authority_bias": {
            "name": "Biais d'autorite",
            "principle": (
                "Les gens accordent plus de credibilite aux experts et "
                "figures d'autorite. Se positionner comme expert du domaine "
                "via l'experience, les donnees et la precision."
            ),
            "formula": (
                "1. Ouvrir avec un fait precis ou une donnee chiffree\n"
                "2. Partager une experience personnelle de terrain\n"
                "3. Donner un conseil actionnable et specifique\n"
                "4. Fermer avec une prise de position claire"
            ),
            "hook_examples": [
                "Apres [X] annees dans [domaine], voici ce que je sais :",
                "J'ai [verbe d'action] [quantite] [objets]. Voici les [N] patterns que j'observe.",
                "Les donnees sont claires : [stat]. Voici ce que ca signifie pour [cible].",
            ],
        },
        "reciprocity": {
            "name": "Reciprocite",
            "principle": (
                "Quand on recoit quelque chose de valeur gratuitement, "
                "on ressent le besoin inconscient de rendre la pareille. "
                "Donner avant de demander."
            ),
            "formula": (
                "1. Offrir une valeur concrete et immediate (framework, template, checklist)\n"
                "2. Rendre le contenu 'sauvegardable' (listes, etapes numerotees)\n"
                "3. Pas de contrepartie explicite dans le corps du post\n"
                "4. CTA doux : 'sauvegardez', 'partagez si utile'"
            ),
            "hook_examples": [
                "Voici le framework exact que j'utilise pour [resultat].",
                "J'aurais paye cher pour cette liste il y a [X] ans.",
                "[N] ressources gratuites qui valent plus qu'une formation a [montant].",
            ],
        },
        "anchoring": {
            "name": "Effet d'ancrage",
            "principle": (
                "Le premier chiffre/information presente sert de point de "
                "reference pour tout ce qui suit. Ancrer haut pour que "
                "la realite semble accessible, ou ancrer bas pour surprendre."
            ),
            "formula": (
                "1. Presenter un chiffre de reference (ancre haute ou basse)\n"
                "2. Reveler le chiffre reel (effet de contraste)\n"
                "3. Expliquer le 'comment' (la methode)\n"
                "4. Rendre le resultat reproductible pour le lecteur"
            ),
            "hook_examples": [
                "Tout le monde pense que [X] coute [montant eleve]. En realite, il suffit de [Y].",
                "Mon premier [X] m'a pris 6 mois. Le dernier ? 2 semaines.",
                "[Grande entreprise] depense [gros montant] pour [X]. Vous pouvez obtenir le meme resultat avec [methode gratuite].",
            ],
        },
        "scarcity_fomo": {
            "name": "Rarete & FOMO",
            "principle": (
                "Ce qui est rare ou limite dans le temps est percu comme "
                "plus desirable. Creer un sentiment d'urgence authentique "
                "pour accelerer la decision."
            ),
            "formula": (
                "1. Etablir la valeur de l'opportunite\n"
                "2. Introduire la contrainte (temps, places, disponibilite)\n"
                "3. Montrer que d'autres en profitent deja\n"
                "4. CTA avec deadline ou limite claire"
            ),
            "hook_examples": [
                "Cette opportunite disparait dans [duree]. Voici pourquoi ca compte.",
                "Seulement [N]% des [cible] connaissent cette strategie. Pour l'instant.",
                "Le marche de [X] change en [date]. Ceux qui se preparent maintenant auront un avantage enorme.",
            ],
        },
        "storytelling_arc": {
            "name": "Arc narratif & empathie neuronale",
            "principle": (
                "Les histoires activent le couplage neuronal : le cerveau "
                "du lecteur reproduit les emotions du narrateur. Une histoire "
                "bien structuree genere 22x plus de memorisation qu'un fait brut."
            ),
            "formula": (
                "1. SITUATION : Contexte relatable (je/on + lieu/moment)\n"
                "2. COMPLICATION : Le probleme ou l'obstacle (tension)\n"
                "3. TOURNANT : Le moment de realisation ou d'action\n"
                "4. RESOLUTION : Le resultat + la lecon\n"
                "5. MIROIR : Relier a la situation du lecteur"
            ),
            "hook_examples": [
                "Il y a [duree], j'etais [situation]. Puis [evenement] a tout change.",
                "Mon client m'a dit une phrase qui m'a cloue sur place :",
                "Assis dans [lieu], j'ai realise que tout ce qu'on m'avait appris sur [X] etait faux.",
            ],
        },
    }

    # --- Emotional triggers per post objective ---

    EMOTIONAL_TRIGGERS = {
        "inspire": {
            "emotions": ["espoir", "admiration", "fierte", "emerveillement"],
            "pattern": "Montrer une transformation ou un accomplissement",
            "words": ["imagine", "possible", "transformer", "accomplir", "reveler"],
        },
        "educate": {
            "emotions": ["curiosite", "surprise", "comprehension", "eureka"],
            "pattern": "Rendre l'invisible visible, simplifier le complexe",
            "words": ["decouvrir", "comprendre", "reveler", "en realite", "voici pourquoi"],
        },
        "provoke": {
            "emotions": ["indignation", "surprise", "remise en question"],
            "pattern": "Challenger une croyance etablie avec des preuves",
            "words": ["mythe", "erreur", "en fait", "contrairement a", "le probleme"],
        },
        "connect": {
            "emotions": ["appartenance", "empathie", "nostalgie", "reconnaissance"],
            "pattern": "Partager une vulnerabilite ou une experience commune",
            "words": ["comme vous", "nous avons tous", "je me souviens", "personne ne parle de"],
        },
        "activate": {
            "emotions": ["urgence", "determination", "motivation", "frustration positive"],
            "pattern": "Creer un moment de decision, pousser a l'action",
            "words": ["maintenant", "arretez de", "commencez", "il est temps", "choisissez"],
        },
    }

    def __init__(self, context: BusinessContext):
        self.context = context

    def generate_post_prompt(
        self,
        topic: str,
        bias: str = "curiosity_gap",
        emotion: str = "educate",
        post_format: str = "story",
    ) -> str:
        """Generate a complete neuro-marketing prompt for post creation.

        Args:
            topic: The subject/theme of the post.
            bias: Cognitive bias to leverage (key from COGNITIVE_BIASES).
            emotion: Emotional trigger to use (key from EMOTIONAL_TRIGGERS).
            post_format: Format du post (story, list, contrarian, tutorial, question).

        Returns:
            A detailed prompt string for the AI agent.
        """
        bias_data = self.COGNITIVE_BIASES.get(bias, self.COGNITIVE_BIASES["curiosity_gap"])
        emotion_data = self.EMOTIONAL_TRIGGERS.get(emotion, self.EMOTIONAL_TRIGGERS["educate"])

        context_block = self.context.to_prompt_block()

        format_instructions = self._get_format_instructions(post_format)

        return f"""Tu es un expert en neuro-marketing applique au contenu LinkedIn.
Tu vas creer un post LinkedIn ultra-engageant en appliquant des principes
neuroscientifiques precis.

{context_block}

---

## Ta mission

Cree un post LinkedIn sur le sujet : **{topic}**

---

## Biais cognitif a utiliser : {bias_data['name']}

**Principe** : {bias_data['principle']}

**Structure a suivre** :
{bias_data['formula']}

**Exemples de hooks** :
{chr(10).join(f'- "{h}"' for h in bias_data['hook_examples'])}

---

## Declencheur emotionnel : {emotion}

**Emotions ciblees** : {', '.join(emotion_data['emotions'])}
**Pattern** : {emotion_data['pattern']}
**Mots-cles a integrer** : {', '.join(emotion_data['words'])}

---

## Format du post

{format_instructions}

---

## Regles d'ecriture neuro-optimisees

1. **Hook (1ere ligne)** : Pattern interrupt. Max 12 mots. Doit arreter le scroll.
   Pas de "Bonjour" ou "Aujourd'hui je vais parler de".
2. **Espacement** : 1 idee = 1 ligne. Lignes de 8-12 mots max.
   Sauter une ligne entre chaque idee.
3. **Rythme** : Alterner phrases courtes (impact) et moyennes (explication).
   Jamais de phrases > 20 mots.
4. **Specifique > Generique** : Chiffres precis, noms concrets, exemples reels.
   "J'ai gagne 47 clients en 3 mois" > "J'ai eu du succes".
5. **Micro-boucles** : Chaque paragraphe doit donner envie de lire le suivant.
   Utiliser des transitions-suspense.
6. **CTA final** : Question ouverte ou micro-engagement.
   Pas de CTA generique ("qu'en pensez-vous ?").
   Preferer : poser un dilemme, demander de choisir, inviter a partager UNE experience.
7. **Hashtags** : 3-5 hashtags pertinents. 1 large (>100K), 2 moyens (10K-100K), 1-2 niche.
8. **Longueur** : 1200-1500 caracteres (sweet spot engagement LinkedIn).
9. **Pas de liens dans le corps** : LinkedIn penalise les liens externes.
   Si besoin, mentionner "lien en commentaire".

{self._get_tone_instructions()}
"""

    def get_bias_catalog(self) -> str:
        """Return a formatted catalog of all available cognitive biases."""
        lines = ["# Catalogue des biais cognitifs disponibles\n"]
        for key, data in self.COGNITIVE_BIASES.items():
            lines.append(f"## `{key}` - {data['name']}")
            lines.append(f"**Principe** : {data['principle']}")
            lines.append(f"**Exemples de hooks** :")
            for h in data["hook_examples"]:
                lines.append(f'  - "{h}"')
            lines.append("")
        return "\n".join(lines)

    def get_emotion_catalog(self) -> str:
        """Return a formatted catalog of all emotional triggers."""
        lines = ["# Catalogue des declencheurs emotionnels\n"]
        for key, data in self.EMOTIONAL_TRIGGERS.items():
            lines.append(f"## `{key}` - {data['pattern']}")
            lines.append(f"**Emotions** : {', '.join(data['emotions'])}")
            lines.append(f"**Mots-cles** : {', '.join(data['words'])}")
            lines.append("")
        return "\n".join(lines)

    def _get_format_instructions(self, post_format: str) -> str:
        """Return structure instructions for the chosen post format."""
        formats = {
            "story": (
                "**Format : HISTOIRE (Storytelling)**\n"
                "- Ligne 1 : Hook emotionnel (pattern interrupt)\n"
                "- Ligne 2-3 : Contexte rapide (situation initiale)\n"
                "- Ligne 4-6 : La complication / le probleme\n"
                "- Ligne 7-9 : Le tournant (realisation, action decisive)\n"
                "- Ligne 10-12 : La resolution + lecon\n"
                "- Ligne 13 : Miroir vers le lecteur (question/CTA)"
            ),
            "list": (
                "**Format : LISTE A VALEUR (Reciprocite)**\n"
                "- Ligne 1 : Hook avec le nombre + la promesse\n"
                "- Ligne 2 : Contexte court (pourquoi cette liste)\n"
                "- Items : Chaque item = emoji + titre court + 1 phrase d'explication\n"
                "- Dernier item = le plus impactant (peak-end rule)\n"
                "- Fin : CTA de sauvegarde/partage"
            ),
            "contrarian": (
                "**Format : PRISE DE POSITION CONTRAIRE**\n"
                "- Ligne 1 : Affirmation provocante (contraire a la norme)\n"
                "- Ligne 2-3 : 'Tout le monde dit [X]. Je pense le contraire.'\n"
                "- Ligne 4-7 : Vos 3 arguments + preuves\n"
                "- Ligne 8-9 : Nuance (pour ne pas aliener)\n"
                "- Ligne 10 : CTA polarisant (etes-vous d'accord ?)"
            ),
            "tutorial": (
                "**Format : MICRO-TUTORIEL (Autorite + Reciprocite)**\n"
                "- Ligne 1 : Hook resultat ('Comment j'ai [resultat] en [temps]')\n"
                "- Ligne 2 : Contexte du probleme\n"
                "- Etapes : Numerotees, courtes, actionnables\n"
                "- Chaque etape : Verbe d'action + detail precis\n"
                "- Fin : Resultat obtenu + CTA sauvegarde"
            ),
            "question": (
                "**Format : QUESTION OUVERTE (Zeigarnik + Curiosite)**\n"
                "- Ligne 1 : Question provocante ou paradoxale\n"
                "- Ligne 2-4 : Contexte qui rend la question pertinente\n"
                "- Ligne 5-7 : Votre reflexion (sans reponse definitive)\n"
                "- Ligne 8 : Relancer avec une 2e question plus precise\n"
                "- Fin : Inviter a repondre en commentaire"
            ),
        }
        return formats.get(post_format, formats["story"])

    def _get_tone_instructions(self) -> str:
        """Generate tone instructions from business context."""
        if not self.context.voice_tone:
            return ""
        lines = ["\n## Ton et style\n"]
        lines.append(f"Adopte un ton **{self.context.voice_tone}**.")
        if self.context.preferred_words:
            lines.append(f"Integre ces mots/expressions : {', '.join(self.context.preferred_words)}")
        if self.context.avoided_words:
            lines.append(f"Evite absolument : {', '.join(self.context.avoided_words)}")
        if not self.context.use_emojis:
            lines.append("N'utilise PAS d'emojis.")
        else:
            lines.append("Utilise les emojis avec parcimonie (max 3-4 par post, aux points cles).")
        return "\n".join(lines)
