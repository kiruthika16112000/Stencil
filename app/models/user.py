import hashlib


class User:
    def __init__(self, username, password_hash, security_question="", security_answer_hash=""):
        self._username = username
        self._password_hash = password_hash
        self._security_question = security_question
        self._security_answer_hash = security_answer_hash

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _hash_answer(answer):
        return hashlib.sha256(answer.strip().lower().encode()).hexdigest()

    @classmethod
    def create(cls, username, password, security_question="", security_answer=""):
        answer_hash = cls._hash_answer(security_answer) if security_answer else ""
        return cls(username, cls.hash_password(password), security_question, answer_hash)

    @property
    def username(self):
        return self._username

    @property
    def password_hash(self):
        return self._password_hash

    @property
    def security_question(self):
        return self._security_question

    def verify_password(self, password):
        return self._password_hash == self.hash_password(password)

    def verify_security_answer(self, answer):
        return bool(self._security_answer_hash) and self._security_answer_hash == self._hash_answer(answer)

    def with_updates(self, username=None, password=None):
        new_username = username or self._username
        new_hash = self.hash_password(password) if password else self._password_hash
        return type(self)(new_username, new_hash, self._security_question, self._security_answer_hash)

    def role(self):
        return "User"

    def to_dict(self):
        return {
            "username": self._username,
            "password_hash": self._password_hash,
            "role": self.role(),
            "security_question": self._security_question,
            "security_answer_hash": self._security_answer_hash,
        }

    @staticmethod
    def from_dict(data):
        cls = Admin if data.get("role") == "Admin" else User
        return cls(
            data["username"],
            data["password_hash"],
            data.get("security_question", ""),
            data.get("security_answer_hash", ""),
        )


class Admin(User):
    def role(self):
        return "Admin"
