import os
from dotenv import load_dotenv

load_dotenv()

MYSQLHOST = os.getenv("MYSQLHOST", "localhost")
MYSQLPORT = int(os.getenv("MYSQLPORT", "3306"))
MYSQLUSER = os.getenv("MYSQLUSER", "root")
MYSQLPASSWORD = os.getenv("MYSQLPASSWORD", "root")
MYSQLDATABASE = os.getenv("MYSQLDATABASE", "green_db")
