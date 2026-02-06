# LinkedIn MCP Server

Serveur MCP (Model Context Protocol) complet pour l'API LinkedIn, construit avec **FastAPI** et le SDK **MCP Python**.

**33 tools MCP** organises en 2 couches :
- **Couche API** (22 tools) : Profils, Posts, Invitations -- operations directes sur l'API LinkedIn
- **Couche Skills** (11 tools) : Neuro-marketing, Copywriting, Engagement, Strategie de contenu -- generation intelligente

## Architecture

```
src/linkedin_mcp/
├── config.py                # Configuration & token storage
├── auth.py                  # OAuth 2.0 3-legged flow
├── linkedin_client.py       # Client HTTP async pour l'API LinkedIn REST
├── fastapi_app.py           # Serveur FastAPI (OAuth callback + REST API)
├── mcp_server.py            # Serveur MCP (33 tools + 3 prompts)
├── plugins/                 # Couche API LinkedIn
│   ├── profiles.py          # Recherche de profils
│   ├── posts.py             # Publication de posts
│   └── invitations.py       # Envoi d'invitations
└── skills/                  # Couche intelligence contenu
    ├── business_context.py  # Chargeur de contexte business (CLAUDE.md)
    ├── neuromarketing.py    # Biais cognitifs & declencheurs emotionnels
    ├── copywriting.py       # Frameworks AIDA, PAS, BAB, 4Ps, APP, SLAP
    ├── engagement.py        # Hooks, CTAs, signaux algorithmiques
    └── content_strategy.py  # Calendrier, piliers, funnel TOFU/MOFU/BOFU
```

## Prerequis

- Python 3.10+
- Une application LinkedIn Developer (https://developer.linkedin.com/)
- Acces a la Community Management API (pour la recherche de profils)

## Installation

```bash
# Cloner le repo
git clone <repo-url>
cd Linkedin_mcp

# Installer les dependances
pip install -e .

# Ou avec requirements.txt
pip install -r requirements.txt
```

## Configuration

### 1. Credentials LinkedIn

```bash
cp .env.example .env
```

Editer `.env` :

```env
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/callback
LINKEDIN_SCOPES=openid profile email w_member_social r_member_social
LINKEDIN_API_VERSION=202601
```

### 2. Contexte Business (CLAUDE.md)

Editez le fichier `CLAUDE.md` a la racine du projet pour personnaliser tous les skills :

```markdown
## Identite
- **Nom / Marque** : MonEntreprise
- **Secteur** : SaaS B2B
- **Titre LinkedIn** : CEO @ MonEntreprise | Expert en IA

## Proposition de valeur
- **Probleme resolu** : Les PME perdent 15h/semaine sur des taches manuelles
- **Solution** : Plateforme IA no-code d'automatisation

## Audience cible
- **ICP** : CTO de PME tech, 50-500 salaries
- **Douleurs principales** : Manque de temps, erreurs manuelles, scaling difficile

## Ton et personnalite
- **Ton de voix** : Expert accessible et direct
- **Mots a utiliser** : automatiser, scaler, ROI, pipeline
- **Mots a eviter** : synergie, disruptif
- **Emojis** : Oui

## Piliers de contenu
1. Expertise technique - tutoriels IA et automatisation
2. Behind the scenes - coulisses de la startup
3. Vision industrie - tendances IA et futur du travail
4. Social proof - resultats clients et temoignages

## Objectifs LinkedIn
- **Objectif principal** : Generer 10 leads qualifies / mois
- **CTA prefere** : Commentez GUIDE pour recevoir le framework
```

Le contexte est charge automatiquement par tous les skills. Il peut aussi etre passe en argument a chaque tool via le parametre `business_context`.

### 3. Obtenir les credentials LinkedIn

1. Allez sur https://developer.linkedin.com/
2. Creez une application
3. Dans l'onglet **Auth**, copiez le Client ID et Client Secret
4. Ajoutez `http://localhost:8000/auth/callback` dans les Redirect URLs
5. Dans l'onglet **Products**, demandez l'acces a **Community Management API**

## Utilisation

### Demarrer le serveur FastAPI (authentification OAuth)

```bash
linkedin-api
# Ou: PYTHONPATH=src uvicorn linkedin_mcp.fastapi_app:app --reload --port 8000
```

Ouvrez http://localhost:8000 puis **Login with LinkedIn**.
Swagger : http://localhost:8000/docs

### Demarrer le serveur MCP

```bash
linkedin-mcp
# Ou: PYTHONPATH=src python -m linkedin_mcp
```

### Configurer dans Claude Desktop

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["-m", "linkedin_mcp"],
      "env": {
        "PYTHONPATH": "/chemin/vers/Linkedin_mcp/src",
        "LINKEDIN_CLIENT_ID": "votre_client_id",
        "LINKEDIN_CLIENT_SECRET": "votre_client_secret"
      }
    }
  }
}
```

---

## Tools MCP : Couche API (22 tools)

### Authentification (2)
| Tool | Description |
|------|-------------|
| `linkedin_auth_status` | Statut d'authentification OAuth2 |
| `linkedin_get_auth_url` | URL d'autorisation LinkedIn |

### Profils (6)
| Tool | Description |
|------|-------------|
| `linkedin_get_my_profile` | Mon profil (OpenID Connect) |
| `linkedin_get_my_profile_details` | Mon profil detaille (/v2/me) |
| `linkedin_get_profile` | Profil par person ID |
| `linkedin_get_connections` | Connexions 1er degre |
| `linkedin_search_people` | Recherche par mots-cles |
| `linkedin_search_connections` | Recherche dans mes connexions |

### Posts (7)
| Tool | Description |
|------|-------------|
| `linkedin_create_text_post` | Post texte (hashtags, mentions) |
| `linkedin_create_link_post` | Post avec lien/article |
| `linkedin_create_image_post` | Post avec image (upload auto) |
| `linkedin_get_my_posts` | Mes publications recentes |
| `linkedin_get_post` | Post par URN |
| `linkedin_delete_post` | Supprimer un post |
| `linkedin_reshare_post` | Repartager un post |

### Invitations (7)
| Tool | Description |
|------|-------------|
| `linkedin_send_invitation` | Invitation par person ID |
| `linkedin_send_invitation_by_email` | Invitation par email |
| `linkedin_get_received_invitations` | Invitations recues |
| `linkedin_get_sent_invitations` | Invitations envoyees |
| `linkedin_accept_invitation` | Accepter |
| `linkedin_ignore_invitation` | Ignorer |
| `linkedin_withdraw_invitation` | Retirer |

---

## Tools MCP : Couche Skills (11 tools)

### Neuro-Marketing (2)
| Tool | Parametres | Description |
|------|-----------|-------------|
| `skill_neuro_post` | `topic`, `bias`, `emotion`, `post_format` | Genere un prompt neuro-optimise |
| `skill_neuro_catalog` | - | Catalogue des biais cognitifs et emotions |

**Biais cognitifs disponibles** : `curiosity_gap`, `loss_aversion`, `social_proof`, `authority_bias`, `reciprocity`, `anchoring`, `scarcity_fomo`, `storytelling_arc`

**Emotions** : `inspire`, `educate`, `provoke`, `connect`, `activate`

**Formats** : `story`, `list`, `contrarian`, `tutorial`, `question`

### Copywriting (3)
| Tool | Parametres | Description |
|------|-----------|-------------|
| `skill_copywriting_post` | `topic`, `framework`, `tone` | Post avec framework copywriting |
| `skill_copywriting_ab_test` | `topic`, `framework_a`, `framework_b` | 2 versions A/B test |
| `skill_copywriting_catalog` | - | Catalogue des 6 frameworks |

**Frameworks** : `aida` (Attention/Interest/Desire/Action), `pas` (Problem/Agitation/Solution), `bab` (Before/After/Bridge), `4ps` (Promise/Picture/Proof/Push), `app` (Agree/Promise/Preview), `slap` (Stop/Look/Act/Purchase)

### Engagement (3)
| Tool | Parametres | Description |
|------|-----------|-------------|
| `skill_engagement_post` | `topic`, `objective`, `hook_style` | Post optimise pour une metrique |
| `skill_engagement_hooks` | - | 8 formules de hooks LinkedIn |
| `skill_engagement_ctas` | - | Strategies CTA par objectif |

**Objectifs** : `comments`, `saves`, `leads`, `shares`, `profile_visits`

**Formules de hooks** : Le Chiffre Choc, L'Anti-Conseil, La Confession, La Question Impossible, Le Comparatif Violent, L'Enumeration Promise, Le Dialogue Direct, L'Observation Silencieuse

### Strategie de Contenu (2)
| Tool | Parametres | Description |
|------|-----------|-------------|
| `skill_content_calendar` | `mode`, `weeks` | Calendrier editorial complet |
| `skill_content_ideas` | `pillar`, `funnel_stage`, `count` | Brainstorming d'idees |

**Modes calendrier** : `growth_mode` (5 posts/sem), `authority_mode` (3/sem), `lead_gen_mode` (4/sem)

**Piliers** : `expertise`, `behind_the_scenes`, `industry_vision`, `social_proof`, `personal_brand`, `curation`

**Funnel** : `tofu` (awareness 40%), `mofu` (consideration 35%), `bofu` (conversion 25%)

### Contexte Business (1)
| Tool | Description |
|------|-------------|
| `skill_show_business_context` | Affiche le contexte business charge |

---

## Prompts MCP (3 assistants pre-configures)

| Prompt | Role |
|--------|------|
| `linkedin_post_assistant` | Assistant creation de posts neuro-marketing |
| `linkedin_network_assistant` | Assistant growth et networking |
| `linkedin_content_strategist` | Assistant strategie de contenu |

---

## Exemples d'utilisation

### Creer un post neuro-marketing

```python
# Via MCP tool
skill_neuro_post(
    topic="Pourquoi 80% des projets IA echouent",
    bias="loss_aversion",
    emotion="provoke",
    post_format="contrarian"
)
# -> Genere un prompt complet, puis utilisez linkedin_create_text_post pour publier
```

### Generer un calendrier editorial

```python
skill_content_calendar(mode="growth_mode", weeks=2)
# -> Plan de 10 posts sur 2 semaines avec hooks, angles, CTAs
```

### A/B test entre frameworks

```python
skill_copywriting_ab_test(
    topic="Comment doubler vos leads LinkedIn en 30 jours",
    framework_a="pas",
    framework_b="aida"
)
# -> 2 versions du meme post + recommandation
```

---

## Endpoints FastAPI

### Authentification
- `GET /auth/login` - Demarrer le flow OAuth2
- `GET /auth/callback` - Callback OAuth2
- `GET /auth/status` - Statut d'authentification
- `POST /auth/logout` - Deconnexion

### Profils
- `GET /api/profiles/me` - Mon profil
- `GET /api/profiles/me/details` - Mon profil detaille
- `GET /api/profiles/search?keywords=...` - Recherche
- `GET /api/profiles/connections` - Mes connexions
- `GET /api/profiles/{person_id}` - Profil par ID

### Posts
- `POST /api/posts/text` - Creer un post texte
- `POST /api/posts/link` - Creer un post avec lien
- `POST /api/posts/image` - Creer un post avec image
- `POST /api/posts/reshare` - Repartager un post
- `GET /api/posts/mine` - Mes posts
- `GET /api/posts/{urn}` - Obtenir un post
- `DELETE /api/posts/{urn}` - Supprimer un post

### Invitations
- `POST /api/invitations/send` - Envoyer une invitation
- `POST /api/invitations/send-by-email` - Invitation par email
- `GET /api/invitations/received` - Invitations recues
- `GET /api/invitations/sent` - Invitations envoyees
- `POST /api/invitations/accept` / `ignore` / `withdraw`

---

## Securite

- Les tokens OAuth2 sont stockes localement dans `token_store.json` (`.gitignore`)
- Les credentials LinkedIn dans `.env` (jamais commites)
- Protection CSRF via le parametre `state`
- Tokens expirent apres 60 jours (rafraichissables)

## Reference API LinkedIn

- [Documentation officielle](https://learn.microsoft.com/en-us/linkedin/)
- [OAuth 2.0 Authorization Code Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Getting Access](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
