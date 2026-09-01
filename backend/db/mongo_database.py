"""
MongoDB Database Manager for WeatherGPT.
Handles database connections, collection initialization, indexes, and CRUD operations
for users, OTP verification records, conversation threads, and message history.
"""
import os
import time
import uuid
import datetime
from typing import Optional, Dict, Any, List, Union
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

class MongoDatabaseManager:
    """Singleton MongoDB Manager for WeatherGPT authentication and assistant history."""
    
    _instance: Optional["MongoDatabaseManager"] = None

    def __init__(self, uri: Optional[str] = None, db_name: str = "weathergpt"):
        self.uri = uri or os.getenv("MONGODB_URI", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "weathergpt")
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_mock = False
        self._connected = False
        self._init_connection()

    @classmethod
    def get_instance(cls, uri: Optional[str] = None, db_name: str = "weathergpt") -> "MongoDatabaseManager":
        if cls._instance is None:
            cls._instance = MongoDatabaseManager(uri=uri, db_name=db_name)
        return cls._instance

    def _init_connection(self):
        """Initializes connection to MongoDB with graceful in-memory fallback for offline test environments."""
        try:
            # Attempt live connection to MongoDB
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=2000,
                maxPoolSize=50,
                retryWrites=True
            )
            # Trigger quick server ping to test connectivity
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.is_mock = False
            self._connected = True
            self._create_indexes()
            print(f"[MongoDB] Successfully connected to MongoDB database: '{self.db_name}'", flush=True)
        except Exception as e:
            # If live Mongo is unreachable (e.g. during local tests without a running daemon), use mongomock
            print(f"[MongoDB] Notice: Could not connect to live MongoDB server ({e}). Initializing resilient in-memory Mongo mock for active runtime.", flush=True)
            try:
                import mongomock
                self.client = mongomock.MongoClient()
                self.db = self.client[self.db_name]
                self.is_mock = True
                self._connected = True
                self._create_indexes()
            except ImportError:
                print(f"[MongoDB] Notice: mongomock not installed, creating in-memory resilient dictionary mock.", flush=True)
                # Pure python dict-based mock fallback
                class DictCollection(dict):
                    def find_one(self, filter=None, *args, **kwargs):
                        return None
                    def find(self, filter=None, *args, **kwargs):
                        return []
                    def insert_one(self, doc):
                        class InsertRes:
                            inserted_id = "mock_id"
                        return InsertRes()
                    def update_one(self, filter, update, upsert=False):
                        pass
                    def delete_one(self, filter):
                        pass
                    def delete_many(self, filter):
                        pass
                    def create_index(self, *args, **kwargs):
                        pass
                class DictDB:
                    def __getitem__(self, name):
                        return DictCollection()
                    def __getattr__(self, name):
                        return DictCollection()
                self.client = None
                self.db = DictDB()
                self.is_mock = True
                self._connected = True
            except Exception as mock_err:
                print(f"[MongoDB] Notice: {mock_err}", flush=True)


    def _create_indexes(self):
        """Creates necessary unique and compound indexes for fast queries and integrity."""
        try:
            if self.db is not None:
                # 1. Users collection
                self.db.users.create_index("email", unique=True)
                
                # 2. OTP collection
                self.db.email_verification_otps.create_index("email")
                
                # 3. Conversations collection
                self.db.conversations.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
                
                # 4. Messages collection
                self.db.messages.create_index([("conversation_id", ASCENDING), ("created_at", ASCENDING)])
                self.db.messages.create_index("user_id")
        except Exception as idx_err:
            print(f"[MongoDB] Warning creating indexes: {idx_err}", flush=True)

    # =========================================================================
    # User Management
    # =========================================================================

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Finds user by normalized lowercase email address."""
        if not email or self.db is None:
            return None
        norm_email = email.strip().lower()
        return self.db.users.find_one({"email": norm_email})

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Finds user by unique user_id string."""
        if not user_id or self.db is None:
            return None
        return self.db.users.find_one({"_id": str(user_id)})

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: Optional[str] = None,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Creates a new registered user in MongoDB with BCRYPT hashed password."""
        norm_email = email.strip().lower()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_id = str(uuid.uuid4())
        
        user_doc = {
            "_id": user_id,
            "email": norm_email,
            "password_hash": password_hash,
            "email_verified": True,
            "name": name or norm_email.split("@")[0],
            "role": role or "user",
            "created_at": now_iso,
            "updated_at": now_iso,
            "last_login_at": now_iso
        }
        self.db.users.insert_one(user_doc)
        return user_doc

    def update_last_login(self, user_id: str):
        """Updates last_login_at timestamp for the user."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.db.users.update_one(
            {"_id": str(user_id)},
            {"$set": {"last_login_at": now_iso, "updated_at": now_iso}}
        )

    # =========================================================================
    # OTP Verification
    # =========================================================================

    def create_or_update_otp(self, email: str, otp_hash: str, expires_at_iso: str) -> Dict[str, Any]:
        """Stores or updates OTP record for email verification."""
        norm_email = email.strip().lower()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Invalidate / remove previous OTP records for this email
        self.db.email_verification_otps.delete_many({"email": norm_email})
        
        otp_id = str(uuid.uuid4())
        doc = {
            "_id": otp_id,
            "email": norm_email,
            "otp_hash": otp_hash,
            "expires_at": expires_at_iso,
            "attempts": 0,
            "verified": False,
            "created_at": now_iso
        }
        self.db.email_verification_otps.insert_one(doc)
        return doc

    def get_otp_record(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves active OTP verification record for email."""
        norm_email = email.strip().lower()
        return self.db.email_verification_otps.find_one({"email": norm_email})

    def increment_otp_attempts(self, email: str) -> int:
        """Increments failed attempt count for an OTP."""
        norm_email = email.strip().lower()
        res = self.db.email_verification_otps.find_one_and_update(
            {"email": norm_email},
            {"$inc": {"attempts": 1}},
            return_document=pymongo.ReturnDocument.AFTER if hasattr(pymongo, 'ReturnDocument') else None
        )
        if res:
            return res.get("attempts", 1)
        record = self.get_otp_record(norm_email)
        return record.get("attempts", 1) if record else 1

    def mark_otp_verified(self, email: str, verification_token: str):
        """Marks OTP as successfully verified and stores the verification token."""
        norm_email = email.strip().lower()
        self.db.email_verification_otps.update_one(
            {"email": norm_email},
            {"$set": {"verified": True, "verification_token": verification_token}}
        )

    def delete_otp_record(self, email: str):
        """Deletes OTP verification record after completion."""
        norm_email = email.strip().lower()
        self.db.email_verification_otps.delete_many({"email": norm_email})

    # =========================================================================
    # Conversation & Message History (User-Owned & IDOR Protected)
    # =========================================================================

    def create_conversation(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Creates a new conversation thread owned strictly by the authenticated user."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        doc = {
            "_id": conv_id,
            "user_id": str(user_id),
            "title": title or "New Weather Conversation",
            "created_at": now_iso,
            "updated_at": now_iso
        }
        self.db.conversations.insert_one(doc)
        return doc

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists all conversations belonging strictly to user_id.
        Prevents IDOR attacks by strictly filtering query by user_id.
        """
        cursor = self.db.conversations.find(
            {"user_id": str(user_id)}
        ).sort("updated_at", DESCENDING).limit(limit)
        
        results = []
        for conv in cursor:
            # Count messages
            msg_count = self.db.messages.count_documents({"conversation_id": conv["_id"]})
            # Get latest message snippet
            last_msg = self.db.messages.find_one(
                {"conversation_id": conv["_id"]},
                sort=[("created_at", DESCENDING)]
            )
            
            results.append({
                "id": conv["_id"],
                "title": conv.get("title", "Weather Conversation"),
                "created_at": conv.get("created_at"),
                "updated_at": conv.get("updated_at"),
                "message_count": msg_count,
                "last_message": last_msg.get("content")[:80] if last_msg else ""
            })
        return results

    def get_conversation_with_messages(self, conv_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single conversation and its full message timeline.
        STRICT IDOR CHECK: Returns None if conversation does not exist or user_id does not match.
        """
        conv = self.db.conversations.find_one({"_id": str(conv_id), "user_id": str(user_id)})
        if not conv:
            return None
            
        messages_cursor = self.db.messages.find(
            {"conversation_id": str(conv_id)}
        ).sort("created_at", ASCENDING)
        
        messages = []
        for m in messages_cursor:
            messages.append({
                "id": m["_id"],
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
                "metadata": m.get("metadata", {}),
                "created_at": m.get("created_at")
            })
            
        return {
            "id": conv["_id"],
            "title": conv.get("title", "Weather Conversation"),
            "created_at": conv.get("created_at"),
            "updated_at": conv.get("updated_at"),
            "messages": messages
        }

    def add_message(
        self,
        conv_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Adds a message to an existing conversation after verifying user ownership.
        Updates the conversation's updated_at timestamp.
        """
        # Strictly verify ownership
        conv = self.db.conversations.find_one({"_id": str(conv_id), "user_id": str(user_id)})
        if not conv:
            return None
            
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        msg_doc = {
            "_id": msg_id,
            "conversation_id": str(conv_id),
            "user_id": str(user_id),
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now_iso
        }
        self.db.messages.insert_one(msg_doc)
        
        # Update conversation updated_at and update title if first message
        update_fields = {"updated_at": now_iso}
        if conv.get("title") in ["New Weather Conversation", "New Chat"] and role == "user":
            clean_title = content.strip().replace("\n", " ")
            if len(clean_title) > 42:
                clean_title = clean_title[:40] + "..."
            update_fields["title"] = clean_title
            
        self.db.conversations.update_one(
            {"_id": str(conv_id)},
            {"$set": update_fields}
        )
        return msg_id

    def delete_conversation(self, conv_id: str, user_id: str) -> bool:
        """
        Deletes a conversation and all its messages.
        STRICT IDOR CHECK: Only deletes if user_id matches conversation owner.
        """
        conv = self.db.conversations.find_one({"_id": str(conv_id), "user_id": str(user_id)})
        if not conv:
            return False
            
        self.db.messages.delete_many({"conversation_id": str(conv_id)})
        self.db.conversations.delete_one({"_id": str(conv_id), "user_id": str(user_id)})
        return True

    def update_conversation_title(self, conv_id: str, user_id: str, new_title: str) -> bool:
        """Updates conversation title with strict user ownership verification."""
        if not new_title or not new_title.strip():
            return False
        res = self.db.conversations.update_one(
            {"_id": str(conv_id), "user_id": str(user_id)},
            {"$set": {"title": new_title.strip()}}
        )
        return res.matched_count > 0
