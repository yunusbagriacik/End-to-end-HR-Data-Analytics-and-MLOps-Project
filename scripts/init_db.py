#Kodda tanımladığımız ORM tablolarını veritabanında gerçekten oluşturmak için bu dosya oluşutuldu.
from app.db.base import Base
from app.db.session import engine
from app.db import models  # noqa: F401Burada models import edilince SQLAlchemy, hangi tabloların var olduğunu öğrenir.


def main():
    Base.metadata.create_all(bind=engine) # Bu Base’den türeyen tüm modelleri bul ve DB’de tablolarını oluştur demek
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
    #Neden ayrı script yaptık? Çünkü tablo oluşturma işlemini tek tuşla yapmak istedik.