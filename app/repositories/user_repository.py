import json
import os

from app.models.user import User


class UserRepository:
    def __init__(self, storage_path):
        self._storage_path = storage_path
        self._users = self._load()

    def _load(self):
        if not os.path.exists(self._storage_path):
            return {}

        with open(self._storage_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        return {username: User.from_dict(data) for username, data in raw.items()}

    def _save(self):
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        raw = {username: user.to_dict() for username, user in self._users.items()}

        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    def exists(self, username):
        return username in self._users

    def add(self, user):
        self._users[user.username] = user
        self._save()

    def get(self, username):
        return self._users.get(username)

    def update(self, old_username, updated_user):
        if old_username != updated_user.username:
            self._users.pop(old_username, None)

        self._users[updated_user.username] = updated_user
        self._save()

    def delete(self, username):
        self._users.pop(username, None)
        self._save()

    def all(self):
        return list(self._users.values())
