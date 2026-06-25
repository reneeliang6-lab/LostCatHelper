from flask import Flask, render_template, request 
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = r"C:\Users\USER\Desktop\lostcats.db"

print("BASE_DIR:", BASE_DIR)
print("DB_PATH:", DB_PATH)

def create_table():
    conn = sqlite3.connect(DB_PATH)
    print(DB_PATH)
    print(os.path.exists(BASE_DIR))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_name TEXT,
            description TEXT,
            location TEXT,
            contact TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    cat_name = request.form["cat_name"]
    description = request.form["description"]
    location = request.form["location"]
    contact = request.form["contact"]

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO cats
        (cat_name, description, location, contact)
        VALUES (?, ?, ?, ?)
        """,
        (cat_name, description, location, contact)
    )

    conn.commit()
    conn.close()

    return render_template("success.html")
  
create_table()

@app.route("/cats")
def cats():

    conn = sqlite3.connect("lostcats.db")

    data = conn.execute(
        "SELECT * FROM cats"
    ).fetchall()

    conn.close()

    return str(data)
    
if __name__ == "__main__":
    app.run(debug=True)