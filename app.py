from flask import Flask, render_template, request 
from flask import send_from_directory
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
print(app.config["UPLOAD_FOLDER"])

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
            contact TEXT,
            photo TEXT
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
    photo = request.files["photo"]
    filename = photo.filename

    if photo.filename != "":
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo.filename))

    if filename != "":
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO cats
        (cat_name, description, location, contact, photo)
        VALUES (?, ?, ?, ?)
        """,
        (cat_name, description, location, contact, filename)
    )

    conn.commit()
    conn.close()

    return render_template("success.html")
  
create_table()

@app.route("/cats")
def cats():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cats")

    cats = cursor.fetchall()

    conn.close()

    return render_template("cats.html", cats=cats)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        
if __name__ == "__main__":
    app.run(debug=True)