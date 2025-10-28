# create_db.py
from database import init_db
import os

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "kb.sqlite")
    init_db(path)
    print("Database initialized at", path)
