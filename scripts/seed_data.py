from datetime import date
from app.db.session import SessionLocal
from app.db.models import Department, Employee


def main():
    db = SessionLocal()

    if db.query(Department).count() > 0:
        print("Seed data already exists.")
        db.close()
        return

    departments = [
        Department(department_name="HR"),
        Department(department_name="Finance"),
        Department(department_name="Technology"),
        Department(department_name="Sales"),
    ]
    db.add_all(departments)
    db.commit()

    dept_map = {d.department_name: d.id for d in db.query(Department).all()}

    employees = [
        Employee(
            employee_code="EMP001",
            first_name="Ayse",
            last_name="Yilmaz",
            gender="F",
            hire_date=date(2021, 5, 10),
            birth_date=date(1994, 3, 15),
            department_id=dept_map["HR"],
            job_title="HR Specialist",
            salary=42000,
            performance_score=3.8,
            engagement_score=4.2,
            absenteeism_rate=0.03,
            overtime_hours_monthly=6,
            promoted_last_2y=False,
            attrition_flag=False,
        ),
        Employee(
            employee_code="EMP002",
            first_name="Mehmet",
            last_name="Demir",
            gender="M",
            hire_date=date(2020, 8, 1),
            birth_date=date(1990, 11, 22),
            department_id=dept_map["Technology"],
            job_title="Data Analyst",
            salary=56000,
            performance_score=3.2,
            engagement_score=2.8,
            absenteeism_rate=0.11,
            overtime_hours_monthly=24,
            promoted_last_2y=False,
            attrition_flag=True,
        ),
    ]

    db.add_all(employees)
    db.commit()
    db.close()
    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()