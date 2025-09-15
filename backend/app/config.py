import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@postgres:5432/ecommdb')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
BACKEND_HOST = os.getenv('BACKEND_HOST', 'http://backend:8000')
