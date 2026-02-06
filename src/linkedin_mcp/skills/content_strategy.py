"""Content strategy skill for LinkedIn.

Plans content calendars, content pillar rotation, funnel-aligned content,
and audience nurture sequences. Uses the business context to generate
a strategic content plan aligned with the user's goals.

Content funnel stages:
- TOFU (Top of Funnel): Awareness, reach, thought leadership
- MOFU (Middle of Funnel): Consideration, trust, authority
- BOFU (Bottom of Funnel): Decision, conversion, action
"""

from __future__ import annotations

from linkedin_mcp.skills.business_context import BusinessContext


class ContentStrategySkill:
    """Generates strategic content planning prompts for LinkedIn."""

    # Content types mapped to funnel stages
    CONTENT_FUNNEL = {
        "tofu": {
            "name": "TOFU - Awareness (Haut de funnel)",
            "objective": "Attirer une audience large, generer de la visibilite",
            "content_types": [
                "Prises de position fortes sur l'industrie",
                "Donnees et statistiques surprenantes",
                "Tendances et predictions du secteur",
                "Mythes debunkes dans votre domaine",
                "Experiences personnelles universelles (echecs, apprentissages)",
                "Questions ouvertes / debats",
            ],
            "tone": "Accessible, provocant, surprenant",
            "cta_type": "Engagement (commentaire, like, partage)",
            "ratio": "40% du contenu",
        },
        "mofu": {
            "name": "MOFU - Consideration (Milieu de funnel)",
            "objective": "Construire la confiance, demontrer l'expertise",
            "content_types": [
                "Tutoriels et how-to detailles",
                "Frameworks et methodologies proprietaires",
                "Etudes de cas clients (anonymisees ou non)",
                "Comparatifs et analyses approfondies",
                "Behind-the-scenes de votre processus",
                "Reponses aux objections courantes",
            ],
            "tone": "Expert, pedagogique, genereux",
            "cta_type": "Sauvegarde, follow, inscription newsletter",
            "ratio": "35% du contenu",
        },
        "bofu": {
            "name": "BOFU - Decision (Bas de funnel)",
            "objective": "Convertir en lead ou client",
            "content_types": [
                "Temoignages et resultats clients",
                "Offres et lead magnets",
                "Avant/apres de vos clients",
                "FAQ et levee d'objections",
                "Posts 'pourquoi travailler avec moi/nous'",
                "Social proof (chiffres, logos, quotes)",
            ],
            "tone": "Confiant, preuve-oriente, call-to-action clair",
            "cta_type": "DM, lien, booking, achat",
            "ratio": "25% du contenu",
        },
    }

    # Content pillar archetypes
    PILLAR_ARCHETYPES = {
        "expertise": {
            "name": "Expertise & savoir-faire",
            "description": "Montrer votre maitrise technique du sujet",
            "post_ideas": [
                "Les [N] erreurs que je vois le plus chez [cible]",
                "Comment [resultat] en [contrainte] (methode complete)",
                "Ce que [N] annees de [domaine] m'ont appris",
                "Le framework que j'utilise pour [probleme]",
                "Analyse detaillee de [tendance du moment]",
            ],
        },
        "behind_the_scenes": {
            "name": "Coulisses & authenticite",
            "description": "Montrer l'humain derriere la marque",
            "post_ideas": [
                "Mon echec de la semaine (et ce que j'en ai tire)",
                "Une journee type dans [mon activite]",
                "La vraie raison pour laquelle j'ai lance [projet]",
                "Ce qu'on ne voit pas quand on est [role]",
                "Le moment ou j'ai failli tout arreter",
            ],
        },
        "industry_vision": {
            "name": "Vision & tendances",
            "description": "Se positionner comme visionnaire du secteur",
            "post_ideas": [
                "Ce que [industrie] sera dans 5 ans (et comment s'y preparer)",
                "Le changement que personne ne voit venir dans [secteur]",
                "Pourquoi [pratique courante] va disparaitre",
                "[Technologie/tendance] va tout changer. Voici comment.",
                "Les 3 signaux faibles que je surveille dans [domaine]",
            ],
        },
        "social_proof": {
            "name": "Preuves & resultats",
            "description": "Demontrer la valeur par les faits",
            "post_ideas": [
                "Comment [client] a obtenu [resultat] en [duree]",
                "Avant/apres : [metrique] de mon client [secteur]",
                "On m'a dit que c'etait impossible. [X] mois plus tard...",
                "[Chiffre] clients, [chiffre] [metrique]. Voici le pattern.",
                "Le message que j'ai recu hier de [client] :",
            ],
        },
        "personal_brand": {
            "name": "Marque personnelle & valeurs",
            "description": "Creer une connexion emotionnelle",
            "post_ideas": [
                "La conviction qui guide toutes mes decisions",
                "Ce que mes parents m'ont appris sur [business lesson]",
                "Je ne serai jamais d'accord avec [position courante]",
                "3 principes non-negociables dans mon travail",
                "La question qu'on me pose le plus (et ma vraie reponse)",
            ],
        },
        "curation": {
            "name": "Curation & ressources",
            "description": "Devenir la source de reference de votre niche",
            "post_ideas": [
                "[N] outils que j'utilise au quotidien (et pourquoi)",
                "Le meilleur [livre/podcast/article] que j'ai lu ce mois",
                "[N] comptes LinkedIn a suivre absolument si vous etes [cible]",
                "La ressource gratuite que j'aurais voulu avoir il y a [X] ans",
                "Mon stack [domaine] : tous les outils que j'utilise",
            ],
        },
    }

    # Weekly content calendar template
    WEEKLY_TEMPLATES = {
        "growth_mode": {
            "name": "Mode Croissance (5 posts/semaine)",
            "description": "Pour accelerer la croissance de l'audience",
            "schedule": {
                "Lundi": {"pillar": "expertise", "funnel": "mofu", "format": "tutorial"},
                "Mardi": {"pillar": "behind_the_scenes", "funnel": "tofu", "format": "story"},
                "Mercredi": {"pillar": "social_proof", "funnel": "bofu", "format": "case_study"},
                "Jeudi": {"pillar": "industry_vision", "funnel": "tofu", "format": "contrarian"},
                "Vendredi": {"pillar": "personal_brand", "funnel": "tofu", "format": "question"},
            },
        },
        "authority_mode": {
            "name": "Mode Autorite (3 posts/semaine)",
            "description": "Pour consolider son positionnement expert",
            "schedule": {
                "Mardi": {"pillar": "expertise", "funnel": "mofu", "format": "tutorial"},
                "Mercredi": {"pillar": "industry_vision", "funnel": "tofu", "format": "contrarian"},
                "Jeudi": {"pillar": "social_proof", "funnel": "bofu", "format": "story"},
            },
        },
        "lead_gen_mode": {
            "name": "Mode Lead Generation (4 posts/semaine)",
            "description": "Pour maximiser la generation de leads",
            "schedule": {
                "Lundi": {"pillar": "expertise", "funnel": "tofu", "format": "list"},
                "Mardi": {"pillar": "social_proof", "funnel": "bofu", "format": "story"},
                "Mercredi": {"pillar": "curation", "funnel": "mofu", "format": "tutorial"},
                "Jeudi": {"pillar": "behind_the_scenes", "funnel": "bofu", "format": "story"},
            },
        },
    }

    def __init__(self, context: BusinessContext):
        self.context = context

    def generate_strategy_prompt(
        self,
        mode: str = "growth_mode",
        weeks: int = 1,
    ) -> str:
        """Generate a content strategy/calendar prompt.

        Args:
            mode: Strategy mode (growth_mode, authority_mode, lead_gen_mode).
            weeks: Number of weeks to plan.
        """
        template = self.WEEKLY_TEMPLATES.get(mode, self.WEEKLY_TEMPLATES["growth_mode"])
        context_block = self.context.to_prompt_block()

        pillars_section = self._build_pillars_section()
        funnel_section = self._build_funnel_section()
        schedule_section = self._build_schedule_section(template, weeks)

        return f"""Tu es un strategiste de contenu LinkedIn senior.
Tu vas creer un plan de contenu detaille et actionnable.

{context_block}

---

## Strategie selectionnee : {template['name']}

{template['description']}

---

{funnel_section}

---

{pillars_section}

---

{schedule_section}

---

## Instructions

Pour chaque post du calendrier, genere :

1. **Jour et heure de publication** (creneau optimal)
2. **Pilier de contenu** utilise
3. **Etape du funnel** (TOFU/MOFU/BOFU)
4. **Hook** (premiere ligne du post, prete a l'emploi)
5. **Angle** (en 1 phrase, l'idee directrice)
6. **Format** (story, liste, tutoriel, question, contrarian)
7. **CTA** specifique
8. **Hashtags** (3-5)
9. **Premier commentaire** a poster par le createur

Assure-toi que :
- La rotation entre piliers est equilibree
- Le ratio TOFU/MOFU/BOFU est respecte (40/35/25)
- Chaque post a un objectif clair et mesurable
- Les hooks sont des pattern interrupts (pas de 'Bonjour' ou 'Aujourd'hui...')
- Le contenu s'adapte au contexte business ci-dessus
"""

    def generate_content_idea_prompt(
        self,
        pillar: str = "expertise",
        funnel_stage: str = "tofu",
        count: int = 10,
    ) -> str:
        """Generate a prompt for brainstorming content ideas.

        Args:
            pillar: Content pillar to focus on.
            funnel_stage: Funnel stage to target.
            count: Number of ideas to generate.
        """
        pillar_data = self.PILLAR_ARCHETYPES.get(pillar, self.PILLAR_ARCHETYPES["expertise"])
        funnel_data = self.CONTENT_FUNNEL.get(funnel_stage, self.CONTENT_FUNNEL["tofu"])
        context_block = self.context.to_prompt_block()

        return f"""Tu es un createur de contenu LinkedIn prolifique.
Genere {count} idees de posts ultra-specifiques et pretes a developper.

{context_block}

---

## Pilier : {pillar_data['name']}
{pillar_data['description']}

Exemples de sujets dans ce pilier :
{chr(10).join(f'- {idea}' for idea in pillar_data['post_ideas'])}

---

## Funnel : {funnel_data['name']}
**Objectif** : {funnel_data['objective']}
**Ton** : {funnel_data['tone']}
**Types de CTA** : {funnel_data['cta_type']}

Types de contenu adaptes :
{chr(10).join(f'- {ct}' for ct in funnel_data['content_types'])}

---

## Format attendu pour chaque idee

Pour chacune des {count} idees, fournis :
1. **Titre de travail** (en 1 ligne)
2. **Hook** (la premiere ligne du post, prete a copier)
3. **Angle** (l'idee directrice en 1-2 phrases)
4. **Format** (story / liste / tutoriel / question / contrarian)
5. **Emotion ciblee** (curiosite, admiration, indignation, etc.)
6. **Difficulte de creation** (facile / moyen / avance)

Les idees doivent etre SPECIFIQUES au contexte business ci-dessus,
pas des sujets generiques. Chaque idee doit etre un post que l'utilisateur
peut developper en 15-30 minutes.
"""

    def _build_pillars_section(self) -> str:
        """Build content pillars section, merging defaults with user's pillars."""
        lines = ["## Piliers de contenu\n"]

        if self.context.content_pillars:
            lines.append("### Piliers personnalises")
            for i, p in enumerate(self.context.content_pillars, 1):
                lines.append(f"{i}. {p}")
            lines.append("\n### Piliers de reference disponibles")

        for key, data in self.PILLAR_ARCHETYPES.items():
            lines.append(f"- **{data['name']}** (`{key}`) : {data['description']}")

        return "\n".join(lines)

    def _build_funnel_section(self) -> str:
        """Build the funnel explanation section."""
        lines = ["## Etapes du funnel\n"]
        for key, data in self.CONTENT_FUNNEL.items():
            lines.append(f"### {data['name']}")
            lines.append(f"- Objectif : {data['objective']}")
            lines.append(f"- Ratio : {data['ratio']}")
            lines.append(f"- Ton : {data['tone']}")
            lines.append(f"- CTA : {data['cta_type']}")
            lines.append("")
        return "\n".join(lines)

    def _build_schedule_section(self, template: dict, weeks: int) -> str:
        """Build the weekly schedule section."""
        lines = [f"## Calendrier ({weeks} semaine{'s' if weeks > 1 else ''})\n"]
        for week in range(1, weeks + 1):
            if weeks > 1:
                lines.append(f"### Semaine {week}")
            for day, config in template["schedule"].items():
                pillar = self.PILLAR_ARCHETYPES.get(config["pillar"], {}).get("name", config["pillar"])
                funnel = config["funnel"].upper()
                fmt = config["format"]
                lines.append(f"- **{day}** : {pillar} | {funnel} | Format: {fmt}")
            lines.append("")
        return "\n".join(lines)
