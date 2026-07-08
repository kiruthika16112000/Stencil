import os
import sys

from app.repositories.settings_repository import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.variant_repository import VariantRepository
from app.services.auth_service import AuthService
from app.services.settings_service import SettingsService
from app.services.variant_service import VariantService
from app.ui.login_window import App

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data", "users.json")
VARIANTS_PATH = os.path.join(BASE_DIR, "data", "variants.json")
SETTINGS_DIR = os.path.join(BASE_DIR, "data", "variant_settings")


def main():
    user_repository = UserRepository(DATA_PATH)
    auth_service = AuthService(user_repository)

    variant_repository = VariantRepository(VARIANTS_PATH)
    variant_service = VariantService(variant_repository)

    settings_repository = SettingsRepository(SETTINGS_DIR)
    settings_service = SettingsService(settings_repository)

    app = App(auth_service, variant_service, settings_service)
    app.mainloop()


if __name__ == "__main__":
    main()
