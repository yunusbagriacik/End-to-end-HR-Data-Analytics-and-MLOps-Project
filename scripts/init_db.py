from app.db.base import Base
from app.db.session import engine
from app.db import models  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()