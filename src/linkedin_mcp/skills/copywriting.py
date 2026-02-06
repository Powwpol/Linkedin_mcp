"""Copywriting frameworks skill for LinkedIn posts.

Provides battle-tested copywriting frameworks adapted for LinkedIn:
- AIDA (Attention, Interest, Desire, Action)
- PAS (Problem, Agitation, Solution)
- BAB (Before, After, Bridge)
- 4Ps (Promise, Picture, Proof, Push)
- SLAP (Stop, Look, Act, Purchase)
- APP (Agree, Promise, Preview)

Each framework includes LinkedIn-specific adaptations, character
constraints, and examples tuned for the platform's algorithm.
"""

from __future__ import annotations

from linkedin_mcp.skills.business_context import BusinessContext


class CopywritingSkill:
    """Generates copywriting-framework-based prompts for LinkedIn posts."""

    FRAMEWORKS = {
        "aida": {
            "name": "AIDA - Attention, Interet, Desir, Action",
            "description": (
                "Le classique du marketing direct adapte a LinkedIn. "
                "Parfait pour les posts qui visent une conversion (lead, inscription, achat)."
            ),
            "structure": {
                "A - Attention (Hook)": (
                    "Ligne 1 : Pattern interrupt. Chiffre choc, question provocante, "
                    "ou affirmation contre-intuitive. Max 12 mots.\n"
                    "Objectif : Arreter le scroll."
                ),
                "I - Interet (Corps haut)": (
                    "Lignes 2-5 : Developper le contexte qui rend le sujet pertinent "
                    "pour le lecteur. Utiliser 'vous/tu' — parler de leur realite, "
                    "pas de la votre.\n"
                    "Objectif : Creer la resonance ('ca me concerne')."
                ),
                "D - Desir (Corps bas)": (
                    "Lignes 6-10 : Montrer la transformation. Peindre le resultat "
                    "avec des details sensoriels et concrets. Utiliser le contraste "
                    "avant/apres.\n"
                    "Objectif : Declencher l'envie ('je veux ca')."
                ),
                "A - Action (CTA)": (
                    "Derniere ligne : CTA clair, specifique et a faible friction. "
                    "Un seul CTA. Pas 'contactez-moi' mais une action micro "
                    "(commenter un mot, DM un emoji).\n"
                    "Objectif : Convertir l'intention en action."
                ),
            },
            "best_for": ["lead generation", "offres", "lancement", "evenements"],
            "example_hook": "93% des CEOs que j'ai rencontres font cette erreur dans leur strategie RH.",
        },
        "pas": {
            "name": "PAS - Probleme, Agitation, Solution",
            "description": (
                "Le framework le plus puissant pour les posts empathiques. "
                "Fonctionne en activant la douleur avant de proposer le remede. "
                "Ideal pour montrer qu'on comprend son audience."
            ),
            "structure": {
                "P - Probleme (Identification)": (
                    "Lignes 1-3 : Nommer le probleme avec les MOTS du lecteur. "
                    "Pas de jargon technique. Decrire la situation telle que le "
                    "lecteur la vit au quotidien.\n"
                    "Objectif : 'C'est exactement mon cas'."
                ),
                "A - Agitation (Amplification)": (
                    "Lignes 4-7 : Amplifier les consequences du probleme. "
                    "Evoquer les couts caches : temps perdu, opportunites ratees, "
                    "stress, impact sur l'equipe/famille. Utiliser des scenarios concrets.\n"
                    "Objectif : Rendre le statu quo intenable."
                ),
                "S - Solution (Resolution)": (
                    "Lignes 8-12 : Presenter la solution comme une evidence. "
                    "Donner 1-3 etapes claires. Montrer un resultat concret "
                    "(chiffres, temoignage). Terminer par un CTA.\n"
                    "Objectif : 'Il y a une solution, et elle est accessible'."
                ),
            },
            "best_for": ["consulting", "services", "coaching", "SaaS", "formation"],
            "example_hook": "Vous passez 3h par jour a eteindre des incendies. Et si le vrai probleme etait ailleurs ?",
        },
        "bab": {
            "name": "BAB - Before, After, Bridge",
            "description": (
                "Le framework de la transformation. Montre l'ecart entre "
                "la situation actuelle et la situation desiree, puis revele "
                "le pont pour y arriver. Tres visuel et emotionnel."
            ),
            "structure": {
                "B - Before (Avant)": (
                    "Lignes 1-4 : Depeindre la situation actuelle du lecteur "
                    "avec des details vivants. Frustrations, blocages, "
                    "symptomes quotidiens. Etre specifique et empathique.\n"
                    "Objectif : Valider la realite du lecteur."
                ),
                "A - After (Apres)": (
                    "Lignes 5-8 : Peindre le tableau de la situation ideale. "
                    "Utiliser le present (pas le conditionnel). Details concrets : "
                    "chiffres, routines, emotions, resultats tangibles.\n"
                    "Objectif : Creer une vision desiree irresistible."
                ),
                "B - Bridge (Pont)": (
                    "Lignes 9-12 : Reveler le chemin. Votre methode, outil, "
                    "ou approche qui fait le lien entre Before et After. "
                    "Montrer que c'est faisable (preuve). CTA pour commencer.\n"
                    "Objectif : 'Voici comment y arriver'."
                ),
            },
            "best_for": ["transformation", "coaching", "resultats clients", "personal branding"],
            "example_hook": "Il y a 18 mois, je scrollais LinkedIn avec le syndrome de l'imposteur.",
        },
        "4ps": {
            "name": "4Ps - Promise, Picture, Proof, Push",
            "description": (
                "Framework oriente conviction. Fait une promesse audacieuse, "
                "la rend tangible, la prouve, puis pousse a l'action. "
                "Puissant pour les posts de vente douce."
            ),
            "structure": {
                "P1 - Promise (Promesse)": (
                    "Lignes 1-2 : Une promesse claire et specifique. "
                    "Pas vague ('ameliorez vos resultats') mais precis "
                    "('doublez vos leads en 30 jours sans ads').\n"
                    "Objectif : Capter l'attention avec un benefice clair."
                ),
                "P2 - Picture (Image mentale)": (
                    "Lignes 3-6 : Aider le lecteur a se VOIR dans le resultat. "
                    "Utiliser des scenarios concrets, des details sensoriels. "
                    "'Imaginez ouvrir votre inbox lundi et trouver...'.\n"
                    "Objectif : Activer le cortex visuel et emotionnel."
                ),
                "P3 - Proof (Preuve)": (
                    "Lignes 7-10 : Prouver la promesse. Chiffres, temoignages, "
                    "etudes de cas, avant/apres. Plus la preuve est specifique "
                    "et verifiable, plus elle est credible.\n"
                    "Objectif : Eliminer le doute."
                ),
                "P4 - Push (Action)": (
                    "Lignes 11-12 : Un CTA a friction minimale. "
                    "Donner une micro-etape immediate ('Commentez GUIDE'), "
                    "pas une decision majeure ('Achetez maintenant').\n"
                    "Objectif : Convertir sans resistance."
                ),
            },
            "best_for": ["vente douce", "lead magnet", "offre limitee", "lancement produit"],
            "example_hook": "Vous pouvez avoir 50 leads qualifies par mois. Sans cold call. Sans ads. Voici comment.",
        },
        "app": {
            "name": "APP - Agree, Promise, Preview",
            "description": (
                "Framework d'ouverture efficace pour des posts educatifs. "
                "Commence par valider une croyance partagee, ajoute une "
                "promesse de valeur, puis donne un apercu du contenu."
            ),
            "structure": {
                "A - Agree (Accord)": (
                    "Lignes 1-2 : Commencer par un constat avec lequel "
                    "le lecteur ne peut qu'etre d'accord. Creer un 'oui' "
                    "mental. Utiliser 'Vous savez que...', 'On est tous d'accord...'.\n"
                    "Objectif : Creer l'alignement initial."
                ),
                "P - Promise (Promesse)": (
                    "Lignes 3-4 : Promettre que ce post va apporter "
                    "une valeur specifique. 'Je vais vous montrer...', "
                    "'Voici exactement comment...'.\n"
                    "Objectif : Justifier la poursuite de la lecture."
                ),
                "P - Preview (Apercu)": (
                    "Lignes 5+ : Donner un apercu structure du contenu "
                    "(liste numerotee, etapes, framework). Le contenu "
                    "doit livrer plus que la promesse.\n"
                    "Objectif : Delivrer la valeur promise."
                ),
            },
            "best_for": ["tutoriels", "listes", "frameworks", "guides"],
            "example_hook": "On est tous d'accord : prospecter a froid en 2024, c'est epuisant.",
        },
        "slap": {
            "name": "SLAP - Stop, Look, Act, Purchase",
            "description": (
                "Framework d'impact immediat. Chaque etape a un seul objectif "
                "sequentiel. Particulierement efficace pour les posts courts "
                "et les carousels."
            ),
            "structure": {
                "S - Stop (Arreter le scroll)": (
                    "Ligne 1 : Une seule ligne choc. Affirmation audacieuse, "
                    "chiffre explosif, ou question existentielle.\n"
                    "Objectif : 0.3 seconde pour capter."
                ),
                "L - Look (Retenir l'attention)": (
                    "Lignes 2-6 : Un developpement qui recompense l'arret. "
                    "Contenu dense, bien espace, chaque ligne apporte une info.\n"
                    "Objectif : Augmenter le dwell time."
                ),
                "A - Act (Declencher une action)": (
                    "Lignes 7-9 : Donner une action concrete et immediate "
                    "que le lecteur peut faire maintenant.\n"
                    "Objectif : Transformer le lecteur passif en acteur."
                ),
                "P - Purchase (Convertir)": (
                    "Derniere ligne : Micro-conversion (follow, save, DM, "
                    "lien en commentaire).\n"
                    "Objectif : Capturer le lead."
                ),
            },
            "best_for": ["posts courts", "impact", "teasing", "carousels"],
            "example_hook": "80% de votre chiffre d'affaires vient de 3 actions. Vous ne faites probablement aucune des 3.",
        },
    }

    def __init__(self, context: BusinessContext):
        self.context = context

    def generate_copywriting_prompt(
        self,
        topic: str,
        framework: str = "pas",
        tone: str | None = None,
    ) -> str:
        """Generate a post prompt using a specific copywriting framework.

        Args:
            topic: The subject of the post.
            framework: Copywriting framework to use (aida, pas, bab, 4ps, app, slap).
            tone: Optional tone override. If None, uses business context tone.
        """
        fw = self.FRAMEWORKS.get(framework, self.FRAMEWORKS["pas"])
        context_block = self.context.to_prompt_block()
        tone_str = tone or self.context.voice_tone or "Expert accessible et direct"

        structure_lines = []
        for step_name, instruction in fw["structure"].items():
            structure_lines.append(f"### {step_name}\n{instruction}\n")

        return f"""Tu es un copywriter senior specialise en contenu LinkedIn B2B.
Tu vas ecrire un post LinkedIn en utilisant le framework **{fw['name']}**.

{context_block}

---

## Framework : {fw['name']}

{fw['description']}

**Ideal pour** : {', '.join(fw['best_for'])}
**Exemple de hook** : "{fw['example_hook']}"

---

## Structure a suivre EXACTEMENT

{chr(10).join(structure_lines)}

---

## Sujet du post : {topic}

## Ton : {tone_str}

---

## Regles de copywriting LinkedIn

1. **1 idee = 1 phrase = 1 ligne** (espacement maximal)
2. **Mots puissants en debut de phrase** (le cerveau retient le premier et dernier mot)
3. **Phrases courtes** : 8-12 mots en moyenne, jamais >20
4. **Voix active** toujours (pas de passif)
5. **Concret > Abstrait** : chiffres, noms, lieux, dates
6. **"Vous/Tu" > "Je"** : ratio 3:1 minimum
7. **Pas de liens** dans le corps du post
8. **3-5 hashtags** a la fin
9. **1200-1500 caracteres** (sweet spot LinkedIn)
10. **Pas de jargon** sauf si le contexte business l'exige

---

## Livrable attendu

1. Le post complet (pret a copier-coller sur LinkedIn)
2. Un premier commentaire du createur (a poster immediatement sous le post)
3. Une variante du hook (version alternative a tester)
"""

    def get_framework_catalog(self) -> str:
        """Return the complete catalog of copywriting frameworks."""
        lines = ["# Catalogue des frameworks de copywriting LinkedIn\n"]
        for key, fw in self.FRAMEWORKS.items():
            lines.append(f"## `{key}` - {fw['name']}")
            lines.append(f"{fw['description']}")
            lines.append(f"**Ideal pour** : {', '.join(fw['best_for'])}")
            lines.append(f"**Exemple** : \"{fw['example_hook']}\"")
            lines.append("")
            for step, desc in fw["structure"].items():
                lines.append(f"  **{step}** : {desc.splitlines()[0]}")
            lines.append("")
        return "\n".join(lines)

    def generate_ab_test_prompt(self, topic: str, framework_a: str, framework_b: str) -> str:
        """Generate two versions of the same post for A/B testing.

        Args:
            topic: Post subject.
            framework_a: First framework to use.
            framework_b: Second framework to use.
        """
        fw_a = self.FRAMEWORKS.get(framework_a, self.FRAMEWORKS["pas"])
        fw_b = self.FRAMEWORKS.get(framework_b, self.FRAMEWORKS["aida"])
        context_block = self.context.to_prompt_block()

        return f"""Tu es un copywriter senior. Tu vas creer 2 versions d'un post
LinkedIn sur le meme sujet pour un A/B test.

{context_block}

## Sujet : {topic}

---

## VERSION A : {fw_a['name']}
{fw_a['description']}
Exemple de hook : "{fw_a['example_hook']}"

Structure :
{chr(10).join(f'- {step}' for step in fw_a['structure'].keys())}

---

## VERSION B : {fw_b['name']}
{fw_b['description']}
Exemple de hook : "{fw_b['example_hook']}"

Structure :
{chr(10).join(f'- {step}' for step in fw_b['structure'].keys())}

---

## Livrable

Pour chaque version :
1. Le post complet
2. Le premier commentaire
3. Les hashtags
4. Prediction : quel type d'engagement cette version devrait generer
   (commentaires vs saves vs shares)

Puis :
5. Ta recommandation : quelle version publier en premier et pourquoi
"""
