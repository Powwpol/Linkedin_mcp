import asyncio
from linkedin_mcp.config import get_settings, get_token_store
from linkedin_mcp.auth import LinkedInAuth

async def main():
    settings = get_settings()
    token_store = get_token_store(settings)
    auth = LinkedInAuth(settings, token_store)
    
    print(f"Current Refresh Token: {token_store.refresh_token[:20]}...")
    try:
        print("Attempting to refresh access token...")
        token_data = await auth.refresh_access_token()
        print("Success! Access token refreshed and stored.")
        print(f"New Access Token: {token_data['access_token'][:20]}...")
    except Exception as e:
        print(f"Error refreshing token: {e}")

if __name__ == "__main__":
    asyncio.run(main())
