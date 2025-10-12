# test_env_load.py
import os
from dotenv import load_dotenv

load_dotenv()  # carrega o .env da pasta atual

print("EMAIL_HOST_PASSWORD:", os.getenv("EMAIL_HOST_PASSWORD"))
