#Model eğitmek için 2 kayıt yetmezdi. Bu yüzden 3000 çalışanlık synthetic veri oluşturduk. Bu dosya:
# Rastgele ama mantıklı çalışan özellikleri üretir
# Bu özelliklere göre churn risk mantığı kurar
# Buna göre attrition_flag üretir
# DB’ye insert eder
import random
from datetime import date, timedelta

from app.db.session import SessionLocal
from app.db.models import Department, Employee


FIRST_NAMES_F = ["Ayse", "Fatma", "Zeynep", "Elif", "Merve", "Esra", "Selin", "Ece"]
FIRST_NAMES_M = ["Mehmet", "Ahmet", "Can", "Ali", "Burak", "Emre", "Mert", "Kerem"]
LAST_NAMES = ["Yilmaz", "Demir", "Kaya", "Celik", "Sahin", "Arslan", "Aydin", "Kurt"]

DEPARTMENTS = ["HR", "Finance", "Technology", "Sales", "Operations", "Marketing"]
JOB_TITLES = {
    "HR": ["HR Specialist", "HR Analyst", "Talent Partner"],
    "Finance": ["Finance Analyst", "Accountant", "Budget Specialist"],
    "Technology": ["Data Analyst", "Data Scientist", "Software Engineer"],
    "Sales": ["Sales Specialist", "Account Manager", "Sales Analyst"],
    "Operations": ["Operations Analyst", "Planning Specialist", "Process Specialist"],
    "Marketing": ["Marketing Analyst", "Brand Specialist", "Growth Analyst"],
}


def random_date(start_year=2018, end_year=2024):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def build_employee(i, dept_id_map):
    gender = random.choice(["F", "M"])
    first_name = random.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M)
    last_name = random.choice(LAST_NAMES)

    dept = random.choice(DEPARTMENTS)
    hire_date = random_date(2018, 2024)
    birth_date = random_date(1980, 2001)
    job_title = random.choice(JOB_TITLES[dept])

    base_salary = {
        "HR": random.randint(35000, 65000),
        "Finance": random.randint(40000, 75000),
        "Technology": random.randint(50000, 95000),
        "Sales": random.randint(35000, 85000),
        "Operations": random.randint(35000, 70000),
        "Marketing": random.randint(38000, 80000),
    }[dept]

    engagement_score = round(random.uniform(2.0, 5.0), 2)
    performance_score = round(random.uniform(2.0, 5.0), 2)
    absenteeism_rate = round(random.uniform(0.0, 0.20), 3)
    overtime_hours_monthly = round(random.uniform(0, 35), 1)
    promoted_last_2y = random.random() < 0.25

    # Basit ama mantıklı attrition logic
    churn_risk = 0.08
    if engagement_score < 3.0:
        churn_risk += 0.25
    if performance_score < 3.0:
        churn_risk += 0.10
    if absenteeism_rate > 0.08:
        churn_risk += 0.18
    if overtime_hours_monthly > 20:
        churn_risk += 0.12
    if not promoted_last_2y:
        churn_risk += 0.07
    if dept in ["Sales", "Operations"]:
        churn_risk += 0.05
    if base_salary < 45000:
        churn_risk += 0.08

    churn_risk = clamp(churn_risk, 0.02, 0.85)
    attrition_flag = random.random() < churn_risk

    return Employee(
        employee_code=f"EMP{i:05d}",
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        hire_date=hire_date,
        birth_date=birth_date,
        department_id=dept_id_map[dept],
        job_title=job_title,
        salary=float(base_salary),
        performance_score=performance_score,
        engagement_score=engagement_score,
        absenteeism_rate=absenteeism_rate,
        overtime_hours_monthly=overtime_hours_monthly,
        promoted_last_2y=promoted_last_2y,
        attrition_flag=attrition_flag,
    )


def main():
    db = SessionLocal()

    existing_departments = db.query(Department).all()
    existing_names = {d.department_name for d in existing_departments}

    missing_departments = [d for d in DEPARTMENTS if d not in existing_names]
    for d in missing_departments:
        db.add(Department(department_name=d))
    db.commit()

    dept_id_map = {d.department_name: d.id for d in db.query(Department).all()}

    db.query(Employee).delete()
    db.commit()

    employees = [build_employee(i, dept_id_map) for i in range(1, 3001)]
    db.add_all(employees)
    db.commit()
    db.close()

    print("3000 synthetic HR employees inserted successfully.")



if __name__ == "__main__":
    main()