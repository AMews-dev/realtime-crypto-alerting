import psycopg2
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker, declarative_base

datebaseurl = "postgresql+psycopg2://postgres:12345@localhost:5433/cryptoDB"




engine = create_engine(datebaseurl)

SessionLocal = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """Prüft beim Serverstart, ob PostgreSQL erreichbar ist."""
    try:
        # Wir öffnen kurz manuell eine Verbindung
        with engine.connect() as connection:
            # Wir senden den simpelsten SQL-Befehl der Welt (gibt einfach nur 1 zurück)
            connection.execute(text("SELECT 1"))
        print("✅ [DATABASE] Verbindung zu PostgreSQL erfolgreich hergestellt!")
        return True
    except Exception as e:
        print("❌ [DATABASE] Verbindung zu PostgreSQL FEHLGESCHLAGEN!")
        print(f"Fehlermeldung: {e}")
        return False