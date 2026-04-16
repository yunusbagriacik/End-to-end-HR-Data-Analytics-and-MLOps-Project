#Veritabanı tablolarının Python class’ları ile tanımlamak için bu dosya oluşturuldu.
from sqlalchemy import String, Integer, Float, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    hire_date: Mapped[Date] = mapped_column(Date, nullable=False)
    birth_date: Mapped[Date] = mapped_column(Date, nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=True)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=True)
    absenteeism_rate: Mapped[float] = mapped_column(Float, nullable=True)
    overtime_hours_monthly: Mapped[float] = mapped_column(Float, nullable=True)
    promoted_last_2y: Mapped[bool] = mapped_column(Boolean, default=False)
    attrition_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    department = relationship("Department")


#Aşağıdaki tablo her API tahminini saklayacak.Yani bir kullanıcı /predict/churn çağırdığında input, skor, label, zaman DB’ye yazılacak.
#Bu çok önemli çünkü dashboard yaparken buradan besleneceğiz, model kullanım geçmişi oluşacak ve gerçek production hissi gelecek
class ChurnPredictionLog(Base):
    __tablename__ = "churn_prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False)
    absenteeism_rate: Mapped[float] = mapped_column(Float, nullable=False)
    overtime_hours_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    promoted_last_2y: Mapped[bool] = mapped_column(Boolean, nullable=False)

    churn_probability: Mapped[float] = mapped_column(Float, nullable=False)
    churn_risk_label: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)