# LinkedIn MCP Server

Serveur MCP (Model Context Protocol) complet pour l'API LinkedIn, construit avec **FastAPI** et le SDK **MCP Python**.

Fournit 3 fonctionnalites principales :
1. **Recherche de profils** - Rechercher et consulter des profils LinkedIn
2. **Publication de posts** - Creer et gerer des publications LinkedIn (texte, lien, image)
3. **Envoi d'invitations** - Envoyer et gerer des demandes de connexion

## Architecture

```
src/linkedin_mcp/
├── __init__.py              # Package init
├── __main__.py              # python -m linkedin_mcp
├── config.py                # Configuration & token storage
├── auth.py                  # OAuth 2.0 3-legged flow
├── linkedin_client.py       # Client HTTP pour l'API LinkedIn
├── fastapi_app.py           # Serveur FastAPI (OAuth callback + REST API)
├── mcp_server.py            # Serveur MCP (22 tools)
└── plugins/
    ├── __init__.py
    ├── profiles.py          # Plugin recherche de profils
    ├── posts.py             # Plugin publication de posts
    └── invitations.py       # Plugin envoi d'invitations
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

Copier le fichier d'exemple et configurer vos credentials :

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

### Obtenir les credentials LinkedIn

1. Allez sur https://developer.linkedin.com/
2. Creez une application
3. Dans l'onglet **Auth**, copiez le Client ID et Client Secret
4. Ajoutez `http://localhost:8000/auth/callback` dans les Redirect URLs
5. Dans l'onglet **Products**, demandez l'acces a **Community Management API**

## Utilisation

### 1. Demarrer le serveur FastAPI (authentification OAuth)

```bash
# Via entry point
linkedin-api

# Ou directement
PYTHONPATH=src uvicorn linkedin_mcp.fastapi_app:app --reload --port 8000
```

Ouvrez http://localhost:8000 dans votre navigateur et cliquez sur **Login with LinkedIn** pour vous authentifier.

Documentation Swagger disponible sur : http://localhost:8000/docs

### 2. Demarrer le serveur MCP

```bash
# Via entry point
linkedin-mcp

# Ou directement
PYTHONPATH=src python -m linkedin_mcp
```

### 3. Configurer dans Claude Desktop

Ajoutez dans `claude_desktop_config.json` :

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

## Tools MCP disponibles (22 tools)

### Authentification
| Tool | Description |
|------|-------------|
| `linkedin_auth_status` | Verifier le statut d'authentification OAuth2 |
| `linkedin_get_auth_url` | Obtenir l'URL d'autorisation LinkedIn |

### Profils (6 tools)
| Tool | Description |
|------|-------------|
| `linkedin_get_my_profile` | Mon profil (OpenID Connect) |
| `linkedin_get_my_profile_details` | Mon profil detaille (/v2/me) |
| `linkedin_get_profile` | Profil par person ID |
| `linkedin_get_connections` | Mes connexions 1er degre |
| `linkedin_search_people` | Recherche de personnes par mots-cles |
| `linkedin_search_connections` | Recherche dans mes connexions |

### Posts (7 tools)
| Tool | Description |
|------|-------------|
| `linkedin_create_text_post` | Publier un post texte |
| `linkedin_create_link_post` | Publier un post avec lien/article |
| `linkedin_create_image_post` | Publier un post avec image |
| `linkedin_get_my_posts` | Mes publications recentes |
| `linkedin_get_post` | Obtenir un post par URN |
| `linkedin_delete_post` | Supprimer un post |
| `linkedin_reshare_post` | Repartager un post |

### Invitations (7 tools)
| Tool | Description |
|------|-------------|
| `linkedin_send_invitation` | Envoyer une invitation par person ID |
| `linkedin_send_invitation_by_email` | Envoyer une invitation par email |
| `linkedin_get_received_invitations` | Invitations recues |
| `linkedin_get_sent_invitations` | Invitations envoyees |
| `linkedin_accept_invitation` | Accepter une invitation |
| `linkedin_ignore_invitation` | Ignorer une invitation |
| `linkedin_withdraw_invitation` | Retirer une invitation envoyee |

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
- `POST /api/invitations/accept` - Accepter
- `POST /api/invitations/ignore` - Ignorer
- `POST /api/invitations/withdraw` - Retirer

## Scopes OAuth2 requis

| Scope | Usage |
|-------|-------|
| `openid` | Authentification OpenID Connect |
| `profile` | Informations de profil basiques |
| `email` | Adresse email |
| `w_member_social` | Creer des posts, commentaires, reactions |
| `r_member_social` | Lire l'activite sociale (Community Management API) |

## Securite

- Les tokens OAuth2 sont stockes localement dans `token_store.json`
- Le fichier `token_store.json` est dans `.gitignore`
- Les credentials LinkedIn doivent etre dans `.env` (jamais commites)
- Le parametre `state` est utilise pour la protection CSRF
- Les tokens expirent apres 60 jours (rafraichissables)

## Reference API LinkedIn

- [Documentation officielle](https://learn.microsoft.com/en-us/linkedin/)
- [OAuth 2.0 Authorization Code Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Getting Access](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
