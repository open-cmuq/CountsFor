from .db import SessionLocal
from .models import CountsFor

def check_countsfor_table():
    db = SessionLocal()
    try:
        records = db.query(CountsFor).all()
        print("Total records in countsfor table:", len(records))
        for rec in records:
            print(rec)
    finally:
        db.close()

if __name__ == "__main__":
    check_countsfor_table()
