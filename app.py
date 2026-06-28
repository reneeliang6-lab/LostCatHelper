from flask import Flask, render_template, request, redirect
from flask import send_from_directory
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
print(app.config["UPLOAD_FOLDER"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lostcats.db")

print("BASE_DIR:", BASE_DIR)
print("DB_PATH:", DB_PATH)

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete old tables (for development only)
    cursor.execute("DROP TABLE IF EXISTS cats")
    cursor.execute("DROP TABLE IF EXISTS sightings")

    # Create cats table
    cursor.execute("""
        CREATE TABLE cats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_name TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            contact TEXT,
            photo TEXT
        )
    """)

    # Create sightings table
    cursor.execute("""
        CREATE TABLE sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_id INTEGER,
            sighting_location TEXT,
            sighting_time TEXT,
            notes TEXT,
            FOREIGN KEY (cat_id) REFERENCES cats(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cats(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_name TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            contact TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Lost'
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
    latitude = request.form["latitude"]
    longitude = request.form["longitude"]
    contact = request.form["contact"]
    photo = request.files["photo"]
    filename = photo.filename

    if filename != "":
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO cats
        (cat_name, description, location, latitude, longitude, contact, photo, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cat_name,
            description,
            location,
            latitude,
            longitude,
            contact,
            filename,
            "Lost"
        )
    )

    conn.commit()
    conn.close()

    return render_template("success.html")
  
create_table()

@app.route("/cats")
def cats():

    search = request.args.get("search")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    if search:
        cursor.execute(
            "SELECT * FROM cats WHERE location LIKE ?",
            ("%" + search + "%",)
        )
    else:
        cursor.execute("SELECT * FROM cats")

    cats = cursor.fetchall()

    conn.close()

    return render_template("cats.html", cats=cats)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM cats WHERE id=?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect("/cats")

@app.route("/edit/<int:id>")
def edit(id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cats WHERE id=?",
        (id,)
    )

    cat = cursor.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        cat=cat
    )

@app.route("/update/<int:id>", methods=["POST"])
def update(id):

    cat_name = request.form["cat_name"]
    description = request.form["description"]
    location = request.form["location"]
    contact = request.form["contact"]

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE cats
        SET
        cat_name=?,
        description=?,
        location=?,
        contact=?
        WHERE id=?
        """,
        (
            cat_name,
            description,
            location,
            contact,
            id
        )
    )

    conn.commit()

    conn.close()

    return redirect("/cats")

@app.route("/poster/<int:id>")
def poster(id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cats WHERE id=?",
        (id,)
    )

    cat = cursor.fetchone()

    conn.close()

    return render_template(
        "poster.html",
        cat=cat
    )

@app.route("/sighting/<int:id>")
def sighting(id):

    return render_template(
        "sighting.html",
        cat_id=id
    )

@app.route("/save_sighting", methods=["POST"])
def save_sighting():

    cat_id = request.form["cat_id"]

    location = request.form["location"]

    time = request.form["time"]

    notes = request.form["notes"]

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sightings
        (cat_id,sighting_location,sighting_time,notes)

        VALUES(?,?,?,?)
        """,
        (
            cat_id,
            location,
            time,
            notes
        )
    )

    conn.commit()

    conn.close()

    return redirect("/cats")

@app.route("/view_sightings/<int:id>")
def view_sightings(id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sightings

        WHERE cat_id=?
        """,
        (id,)
    )

    sightings = cursor.fetchall()

    conn.close()

    return render_template(
        "sightings.html",
        sightings=sightings
    )

@app.route("/found/<int:id>")
def found(id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "UPDATE cats SET status='Found' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/cats")

@app.route("/")
def home():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cats")
    total_cats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cats WHERE status='Found'")
    found_cats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sightings")
    total_sightings = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_cats=total_cats,
        found_cats=found_cats,
        total_sightings=total_sightings
    )

if __name__ == "__main__":
    app.run(debug=True)