#!/usr/bin/env python
import os
import sys


def main():
    app_env = os.getenv("APP_ENV", "development").lower()
    settings_module = "config.settings.prod" if app_env == "production" else "config.settings.dev"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
