import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from datetime import datetime


class SupabaseService:
    def __init__(self):
        self.client = None
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        # Only try to connect if we have real credentials (not placeholders)
        if url and key and not key.startswith("your-"):
            try:
                self.client: Client = create_client(url, key)
            except Exception as e:
                print(f"Warning: Supabase connection failed: {e}")
                self.client = None

        if not self.client:
            print("Info: Supabase not configured. Chat history will not persist (this is OK for now).")

    async def save_message(
        self,
        user_id: Optional[str],
        message: str,
        sender: str  # "user" or "ai"
    ) -> bool:
        """Save a chat message to the database."""
        if not self.client:
            return False

        try:
            self.client.table("chat_logs").insert({
                "user_id": user_id,
                "message": message,
                "sender": sender,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False

    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get recent conversation history for a user."""
        if not self.client:
            return []

        try:
            result = self.client.table("chat_logs") \
                .select("message, sender, timestamp") \
                .eq("user_id", user_id) \
                .order("timestamp", desc=False) \
                .limit(limit) \
                .execute()

            # Convert to the format expected by AI service
            history = []
            for row in result.data:
                role = "assistant" if row["sender"] == "ai" else "user"
                history.append({
                    "role": role,
                    "content": row["message"]
                })

            return history
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user details."""
        if not self.client:
            return None

        try:
            result = self.client.table("users") \
                .select("*") \
                .eq("id", user_id) \
                .single() \
                .execute()
            return result.data
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    async def create_or_update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> bool:
        """Create or update a user record."""
        if not self.client:
            return False

        try:
            self.client.table("users").upsert({
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": "patient"
            }).execute()
            return True
        except Exception as e:
            print(f"Error upserting user: {e}")
            return False


# Singleton instance
supabase_service = SupabaseService()
