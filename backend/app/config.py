import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/greenwatch")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
