#Bu dosyayı tüm uygulamanın ayarlarını tek merkezden yönetmek için oluşturduk.
#Burada BaseSettings, .env dosyasından veri okumamızı sağlar.
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings): #Bu sınıf, çevresel değişkenleri Python nesnesine çevirir.
    ##Bunlar .env içindeki değerlerle doldurulur.
    app_name: str = "People Analytics MLOps"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    #Bunlar .env içindeki değerlerle doldurulur.
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore") #.env dosyasını oku
                                                                       #fazladan alan varsa problem çıkarma


settings = Settings() #sınıftan instance alıp her yerde kullanacağız.
                      # from app.core.config import settings