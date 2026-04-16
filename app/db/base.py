#SQLAlchemy ORM’de tüm tablo sınıflarının türeyeceği ortak temel sınıfı vermek için bu dosya oluşturuldu.
from sqlalchemy.orm import DeclarativeBase

# Benim tüm ORM tablolarım bu "Base" sınıfından türeyecek.
# Örn: class Employee(Base): dediğimizde SQLAlchemy anlıyor ki bu bir ORM tablosu.
class Base(DeclarativeBase):
    pass