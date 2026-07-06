from app.models.user import User, Admin
from app.services.password_policy import validate_password


class AuthError(Exception):
    pass


def _require_valid_password(password):
    issues = validate_password(password)

    if issues:
        raise AuthError("Password must contain " + ", ".join(issues) + ".")


class AuthService:
    def __init__(self, user_repository):
        self._repository = user_repository
        self._current_user = None

    def register(self, username, password, is_admin=False, security_question="", security_answer=""):
        username = username.strip()

        if not username or not password:
            raise AuthError("Username and password are required.")

        if not security_question or not security_answer.strip():
            raise AuthError("A security question and answer are required for password recovery.")

        if self._repository.exists(username):
            raise AuthError(f"Username '{username}' already exists.")

        _require_valid_password(password)

        user_cls = Admin if is_admin else User
        self._repository.add(user_cls.create(username, password, security_question, security_answer))

    def login(self, username, password):
        user = self._repository.get(username.strip())

        if not user or not user.verify_password(password):
            raise AuthError("Invalid username or password.")

        self._current_user = user
        return user

    def logout(self):
        self._current_user = None

    def update_profile(self, current_password, new_username=None, new_password=None):
        user = self._current_user

        if not user:
            raise AuthError("No user is currently logged in.")

        if not user.verify_password(current_password):
            raise AuthError("Current password is incorrect.")

        new_username = (new_username or user.username).strip()

        if not new_username:
            raise AuthError("Username cannot be empty.")

        if new_username != user.username and self._repository.exists(new_username):
            raise AuthError(f"Username '{new_username}' already exists.")

        if new_password:
            _require_valid_password(new_password)

        updated_user = user.with_updates(username=new_username, password=new_password or None)
        self._repository.update(user.username, updated_user)
        self._current_user = updated_user
        return updated_user

    def get_security_question(self, username):
        user = self._repository.get(username.strip())

        if not user:
            raise AuthError("No account found with that username.")

        return user.security_question

    def reset_password(self, username, security_answer, new_password):
        user = self._repository.get(username.strip())

        if not user:
            raise AuthError("No account found with that username.")

        if not user.verify_security_answer(security_answer):
            raise AuthError("Security answer is incorrect.")

        if not new_password:
            raise AuthError("New password is required.")

        _require_valid_password(new_password)

        updated_user = user.with_updates(password=new_password)
        self._repository.update(user.username, updated_user)

    def list_users(self):
        if not self._current_user or self._current_user.role() != "Admin":
            raise AuthError("Only admins can view the user list.")

        return self._repository.all()

    def admin_delete_user(self, username):
        if not self._current_user or self._current_user.role() != "Admin":
            raise AuthError("Only admins can delete other users.")

        if username == self._current_user.username:
            raise AuthError("Admins cannot delete their own account.")

        if not self._repository.exists(username):
            raise AuthError(f"User '{username}' does not exist.")

        self._repository.delete(username)

    @property
    def current_user(self):
        return self._current_user
