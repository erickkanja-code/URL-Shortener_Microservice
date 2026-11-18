"""Application settings, read once from the environment.

Inside Docker, the values come from the environment that Docker Compose
provides. When running locally, they are loaded from the project's `.env`
file. Real environment variables always take priority over `.env`.

Every other module imports its settings from here, so configuration is
read in exactly one place.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))