import os
import sys

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.ui.login_window import App

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data", "users.json")


def main():
    repository = UserRepository(DATA_PATH)
    auth_service = AuthService(repository)
    app = App(auth_service)
    app.mainloop()


if __name__ == "__main__":
    main()
