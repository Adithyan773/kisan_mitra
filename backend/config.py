from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    google_cloud_project: str
    gemini_api_key: str 
    postgres_url: str
    market_prices_search_engine_id:str
    gov_schemes_search_engine_id: str
    weather_search_engine_id: str

    class Config:
        env_file = ".env"

settings = Settings()