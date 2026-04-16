#Bu dosya DB’ye bağlanmak için yazıldı.
#Her scriptte ve her API fonksiyonunda tekrar tekrar bağlantı kurma mantığını dağınık yazmamak için oluşturduk.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.database_url, echo=False) #DB URL’yi alır SQLAlchemy engine oluşturur. engine, bağlantı altyapısıdır. DB ile konuşan ana motor gibidir.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #Session, veritabanı ile aktif çalışma oturumudur.
                                                                            #db = SessionLocal() diyerek veri ekleyebilir, silebilir, sorgulayabilirsin.
