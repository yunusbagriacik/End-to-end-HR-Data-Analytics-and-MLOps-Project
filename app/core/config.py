#Bu dosyayı tüm uygulamanın ayarlarını tek merkezden yönetmek için oluşturduk.
#Burada BaseSettings, .env dosyasından veri okumamızı sağlar.
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings): #Bu sınıf, çevresel değişkenleri Python nesnesine çevirir.
    ##Bunlar .env içindeki değerlerle doldurulur.
    database_url: str | None = None # Cloud Run ilk deploy için DB zorunlu olmasın diye None yapıldı
    churn_threshold: float = 0.33692988753318787 # Modelin 0/1 kararını verdiği eşik.

    mlflow_tracking_uri: str = "file:///app/mlruns" # Localde farklı, Docker içinde farklı.
    mlflow_model_uri: str = "models:/hr_churn_model@production" # production alias’lı modeli okur
    local_model_path: str = "artifacts/churn_model.joblib" # MLflow çalışmazsa fallback olarak kullanılacak model dosyası.

    # ENV_FILE değişkeni verilirse onu okur.
    # Verilmezse default olarak .env okur.
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    ) #.env dosyasını oku fazladan alan varsa problem çıkarma


settings = Settings() #sınıftan instance alıp her yerde kullanacağız.
                      # from app.core.config import settings