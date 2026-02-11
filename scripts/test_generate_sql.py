from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.ollama_service import OllamaService

load_dotenv()

cfg = ConfigManager().load()

svc = OllamaService(database_url=cfg.database_url)

sql = svc.generate_sql(
    question="Donne le chiffre d'affaires total par catégorie",
    language="FR",
)

print(sql)