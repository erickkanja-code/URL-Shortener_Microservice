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

# JWT settings. The secret key signs every token: anyone who has it can
# create valid tokens, so it must stay secret and never be committed.
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Rate limiting. Counters are kept in memory by default (fine for tests and a
# single process). Docker points this at Redis, so all processes share the
# same counters and they survive restarts.
RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
LOGIN_RATE_LIMIT = "5/minute"