"""Business context loader for LinkedIn MCP Skills.

Reads the business context from CLAUDE.md at the project root,
from an environment variable, or from the agent's system prompt.
This context is injected into every skill prompt so the generated
content is always aligned with the user's brand, audience, and goals.

Priority order:
1. Explicit context passed as function argument
2. CLAUDE.md file at project root
3. BUSINESS_CONTEXT_PATH env var pointing to a custom file
4. Minimal fallback (generic context)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BusinessContext:
    """Structured business context injected into skill prompts.

    All fields are optional -- skills degrade gracefully when fields
    are missing, using sensible defaults in their prompts.
    """

    # Identity
    brand_name: str = ""
    linkedin_title: str = ""
    sector: str = ""
    company_size: str = ""

    # Value proposition
    problem_solved: str = ""
    solution: str = ""
    differentiation: str = ""
    social_proof: str = ""

    # Target audience
    icp: str = ""
    pain_points: list[str] = field(default_factory=list)
    aspirations: str = ""
    awareness_level: str = ""

    # Tone
    voice_tone: str = ""
    preferred_words: list[str] = field(default_factory=list)
    avoided_words: list[str] = field(default_factory=list)
    use_emojis: bool = True

    # Content pillars
    content_pillars: list[str] = field(default_factory=list)

    # Goals
    primary_goal: str = ""
    kpi: str = ""
    preferred_cta: str = ""

    # Assets
    website_url: str = ""
    lead_magnet_url: str = ""
    booking_url: str = ""

    # Raw markdown (for skills that want the full context)
    raw_markdown: str = ""

    def has_context(self) -> bool:
        """Return True if any meaningful business context is loaded."""
        return bool(self.brand_name or self.sector or self.icp or self.raw_markdown)

    def to_prompt_block(self) -> str:
        """Serialize the context into a prompt-friendly block.

        Returns a structured text block that can be prepended to any
        skill prompt to inject business context.
        """
        if not self.has_context():
            return (
                "[Aucun contexte business detecte. Le contenu sera generique. "
                "Pour personnaliser, remplissez le fichier CLAUDE.md a la racine du projet.]"
            )

        lines = ["## Contexte Business de l'utilisateur\n"]

        if self.brand_name:
            lines.append(f"- **Marque** : {self.brand_name}")
        if self.linkedin_title:
            lines.append(f"- **Titre** : {self.linkedin_title}")
        if self.sector:
            lines.append(f"- **Secteur** : {self.sector}")
        if self.company_size:
            lines.append(f"- **Taille** : {self.company_size}")

        if self.problem_solved or self.solution:
            lines.append("\n### Proposition de valeur")
            if self.problem_solved:
                lines.append(f"- Probleme : {self.problem_solved}")
            if self.solution:
                lines.append(f"- Solution : {self.solution}")
            if self.differentiation:
                lines.append(f"- Differentiation : {self.differentiation}")
            if self.social_proof:
                lines.append(f"- Preuves : {self.social_proof}")

        if self.icp or self.pain_points:
            lines.append("\n### Audience cible")
            if self.icp:
                lines.append(f"- ICP : {self.icp}")
            if self.pain_points:
                lines.append(f"- Douleurs : {', '.join(self.pain_points)}")
            if self.aspirations:
                lines.append(f"- Aspirations : {self.aspirations}")
            if self.awareness_level:
                lines.append(f"- Niveau de conscience : {self.awareness_level}")

        if self.voice_tone:
            lines.append(f"\n### Ton : {self.voice_tone}")
            if self.preferred_words:
                lines.append(f"- Mots preferes : {', '.join(self.preferred_words)}")
            if self.avoided_words:
                lines.append(f"- Mots a eviter : {', '.join(self.avoided_words)}")

        if self.content_pillars:
            lines.append("\n### Piliers de contenu")
            for i, pillar in enumerate(self.content_pillars, 1):
                lines.append(f"{i}. {pillar}")

        if self.primary_goal:
            lines.append(f"\n### Objectif : {self.primary_goal}")
            if self.kpi:
                lines.append(f"- KPI : {self.kpi}")
            if self.preferred_cta:
                lines.append(f"- CTA prefere : {self.preferred_cta}")

        if self.website_url or self.lead_magnet_url or self.booking_url:
            lines.append("\n### Liens")
            if self.website_url:
                lines.append(f"- Site : {self.website_url}")
            if self.lead_magnet_url:
                lines.append(f"- Lead magnet : {self.lead_magnet_url}")
            if self.booking_url:
                lines.append(f"- Booking : {self.booking_url}")

        return "\n".join(lines)


def _parse_md_value(text: str, label: str) -> str:
    """Extract a value from markdown like '- **Label** : value'."""
    for line in text.splitlines():
        if label.lower() in line.lower() and ":" in line:
            return line.split(":", 1)[1].strip().strip("[]")
    return ""


def _parse_md_list_section(text: str, header: str) -> list[str]:
    """Extract numbered/bulleted list items under a markdown header."""
    items = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if header.lower() in stripped.lower() and stripped.startswith("#"):
            in_section = True
            continue
        if in_section:
            if stripped.startswith("#"):
                break  # Next section
            if stripped.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                # Clean the prefix
                content = stripped.lstrip("-*0123456789. ").strip()
                if content and not content.startswith("["):
                    items.append(content)
    return items


def _parse_comma_list(value: str) -> list[str]:
    """Split a comma-separated string into a list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_context_from_markdown(md_text: str) -> BusinessContext:
    """Parse a CLAUDE.md file into a BusinessContext object."""
    ctx = BusinessContext(raw_markdown=md_text)

    # Identity
    ctx.brand_name = _parse_md_value(md_text, "Nom / Marque")
    ctx.linkedin_title = _parse_md_value(md_text, "Titre LinkedIn")
    ctx.sector = _parse_md_value(md_text, "Secteur")
    ctx.company_size = _parse_md_value(md_text, "Taille entreprise")

    # Value prop
    ctx.problem_solved = _parse_md_value(md_text, "Probleme resolu")
    ctx.solution = _parse_md_value(md_text, "Solution")
    ctx.differentiation = _parse_md_value(md_text, "Differentiation")
    ctx.social_proof = _parse_md_value(md_text, "Preuve sociale")

    # Audience
    ctx.icp = _parse_md_value(md_text, "ICP")
    pain_raw = _parse_md_value(md_text, "Douleurs principales")
    ctx.pain_points = _parse_comma_list(pain_raw)
    ctx.aspirations = _parse_md_value(md_text, "Aspirations")
    ctx.awareness_level = _parse_md_value(md_text, "Niveau de conscience")

    # Tone
    ctx.voice_tone = _parse_md_value(md_text, "Ton de voix")
    ctx.preferred_words = _parse_comma_list(_parse_md_value(md_text, "Mots a utiliser"))
    ctx.avoided_words = _parse_comma_list(_parse_md_value(md_text, "Mots a eviter"))
    emoji_val = _parse_md_value(md_text, "Emojis").lower()
    ctx.use_emojis = emoji_val != "non"

    # Content pillars
    ctx.content_pillars = _parse_md_list_section(md_text, "## Piliers de contenu")

    # Goals
    ctx.primary_goal = _parse_md_value(md_text, "Objectif principal")
    ctx.kpi = _parse_md_value(md_text, "KPI")
    ctx.preferred_cta = _parse_md_value(md_text, "CTA prefere")

    # Assets
    ctx.website_url = _parse_md_value(md_text, "Site web")
    ctx.lead_magnet_url = _parse_md_value(md_text, "Lead magnet")
    ctx.booking_url = _parse_md_value(md_text, "Calendly / Booking")

    return ctx


def load_business_context(explicit_context: str | None = None) -> BusinessContext:
    """Load business context using the priority chain.

    Args:
        explicit_context: If provided, parse this markdown directly
                          instead of reading from file.

    Returns:
        A populated BusinessContext (may be empty if no source found).
    """
    # 1. Explicit context
    if explicit_context:
        return _parse_context_from_markdown(explicit_context)

    # 2. CLAUDE.md at project root (cwd)
    claude_md = Path.cwd() / "CLAUDE.md"
    if claude_md.exists():
        try:
            return _parse_context_from_markdown(claude_md.read_text(encoding="utf-8"))
        except OSError:
            pass

    # 3. BUSINESS_CONTEXT_PATH env var
    env_path = os.environ.get("BUSINESS_CONTEXT_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            try:
                return _parse_context_from_markdown(p.read_text(encoding="utf-8"))
            except OSError:
                pass

    # 4. Fallback
    return BusinessContext()
