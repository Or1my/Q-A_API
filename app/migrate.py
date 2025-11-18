from database import engine, Base
import models

def migrate():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Миграция завершена")

if __name__ == "__main__":
    migrate()