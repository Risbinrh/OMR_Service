"""
Answer Key Storage System
Simple JSON-based storage for answer keys
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from app.models import AnswerKey, AnswerKeyCreate


class AnswerKeyStorage:
    """Simple JSON-based storage for answer keys"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        self.index_file = storage_dir / "index.json"

        # Load or create index
        if self.index_file.exists():
            with open(self.index_file, "r") as f:
                self.index = json.load(f)
        else:
            self.index = {}
            self._save_index()

    def _save_index(self):
        """Save index to disk"""
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def create_answer_key(self, answer_key_data: AnswerKeyCreate) -> AnswerKey:
        """Create a new answer key"""
        key_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()

        answer_key = AnswerKey(
            id=key_id,
            name=answer_key_data.name,
            answers=answer_key_data.answers,
            metadata=answer_key_data.metadata,
            created_at=created_at,
            total_questions=len(answer_key_data.answers),
        )

        # Save to file
        key_file = self.storage_dir / f"{key_id}.json"
        with open(key_file, "w") as f:
            json.dump(answer_key.dict(), f, indent=2)

        # Update index
        self.index[key_id] = {
            "name": answer_key.name,
            "file": str(key_file),
            "created_at": created_at,
            "total_questions": len(answer_key_data.answers),
        }
        self._save_index()

        return answer_key

    def get_answer_key(self, key_id: str) -> Optional[AnswerKey]:
        """Get answer key by ID"""
        if key_id not in self.index:
            return None

        key_file = Path(self.index[key_id]["file"])
        if not key_file.exists():
            return None

        with open(key_file, "r") as f:
            data = json.load(f)

        return AnswerKey(**data)

    def list_answer_keys(self) -> List[AnswerKey]:
        """List all answer keys"""
        keys = []

        for key_id in self.index:
            answer_key = self.get_answer_key(key_id)
            if answer_key:
                keys.append(answer_key)

        return sorted(keys, key=lambda k: k.created_at, reverse=True)

    def delete_answer_key(self, key_id: str) -> bool:
        """Delete an answer key"""
        if key_id not in self.index:
            return False

        # Delete file
        key_file = Path(self.index[key_id]["file"])
        if key_file.exists():
            key_file.unlink()

        # Remove from index
        del self.index[key_id]
        self._save_index()

        return True

    def update_answer_key(self, key_id: str, updates: Dict) -> Optional[AnswerKey]:
        """Update an existing answer key"""
        answer_key = self.get_answer_key(key_id)
        if not answer_key:
            return None

        # Update fields
        if "name" in updates:
            answer_key.name = updates["name"]
        if "answers" in updates:
            answer_key.answers = updates["answers"]
            answer_key.total_questions = len(updates["answers"])
        if "metadata" in updates:
            answer_key.metadata = updates["metadata"]

        # Save updated key
        key_file = self.storage_dir / f"{key_id}.json"
        with open(key_file, "w") as f:
            json.dump(answer_key.dict(), f, indent=2)

        # Update index
        self.index[key_id]["name"] = answer_key.name
        self.index[key_id]["total_questions"] = answer_key.total_questions
        self._save_index()

        return answer_key
