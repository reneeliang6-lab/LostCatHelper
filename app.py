from flask import Flask, render_template, request, redirect
from flask import send_from_directory
from werkzeug.utils import secure_filename
import uuid
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
print(app.config["UPLOAD_FOLDER"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lostcats.db")

print("BASE_DIR:", BASE_DIR)
print("DB_PATH:", DB_PATH)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create sightings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_id INTEGER,
            sighting_location TEXT,
            sighting_time TEXT,
            notes TEXT,
            FOREIGN KEY (cat_id) REFERENCES cats(id)
        )
    """)

    # Create cats table
    cursor.execute("""
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

    # Check whether the status column exists
    cursor.execute("PRAGMA table_info(cats)")
    columns = [column[1] for column in cursor.fetchall()]

    if "status" not in columns:
        cursor.execute(
            "ALTER TABLE cats ADD COLUMN status TEXT DEFAULT 'Lost'"
        )

    conn.commit()
    conn.close()

@app.route("/submit", methods=["POST"])
def submit():
    cat_name = request.form["cat_name"].strip()
    description = request.form["description"].strip()
    location = request.form["location"].strip()
    latitude = request.form["latitude"].strip()
    longitude = request.form["longitude"].strip()
    contact = request.form["contact"].strip()
    photo = request.files["photo"]
    filename = ""
    if photo.filename != "":
        filename = str(uuid.uuid4()) + "_" + secure_filename(photo.filename)
    # Check if an image file was uploaded
    if photo.filename == "":
        return "Please upload a photo of the cat."

    if not allowed_file(photo.filename):
        return "Only PNG, JPG, JPEG, and GIF image files are allowed."
    # Validate required fields
    if not cat_name:
        return "Cat name is required."

    if not description:
        return "Description is required."

    if not location:
        return "Location is required."

    if not contact:
        return "Contact information is required."

    # Validate coordinates
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return "Invalid latitude or longitude."

    try:
        if filename != "":
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    except Exception as e:
        return f"Upload failed: {e}"

    try:
        conn = get_db_connection()

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

    except sqlite3.Error as e:
        return f"Database Error: {e}"

    finally:
        conn.close()

    return render_template("success.html")
  
@app.route("/cats")
def cats():

    search = request.args.get("search")
    status = request.args.get("status")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM cats WHERE 1=1"
    parameters = []

    if search:
        query += """
            AND (
                cat_name LIKE ?
                OR description LIKE ?
                OR location LIKE ?
            )
        """
        parameters.extend([
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ])

    if status:
        query += " AND status=?"
        parameters.append(status)

    query += " ORDER BY status ASC, id DESC"

    cursor.execute(query, parameters)

    cats = cursor.fetchall()

    conn.close()

    return render_template(
        "cats.html",
        cats=cats
    )

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the photo filename
    cursor.execute(
        "SELECT photo FROM cats WHERE id=?",
        (id,)
    )

    photo = cursor.fetchone()

    if photo is None:
        conn.close()
        return "Cat not found."

    # Delete the image file
    if photo[0]:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], photo[0])

        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the database record
    cursor.execute(
        "DELETE FROM cats WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/cats")

@app.route("/edit/<int:id>")
def edit(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cats WHERE id=?",
        (id,)
    )

    cat = cursor.fetchone()

    conn.close()

    if cat is None:
        return "Cat not found."

    return render_template(
        "edit.html",
        cat=cat
    )

@app.route("/update/<int:id>", methods=["POST"])
def update(id):

    cat_name = request.form["cat_name"].strip()
    description = request.form["description"].strip()
    location = request.form["location"].strip()
    contact = request.form["contact"].strip()

    conn = get_db_connection()

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

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cats WHERE id=?",
        (id,)
    )

    cat = cursor.fetchone()

    conn.close()

    if cat is None:
        return "Cat not found."

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

    conn = get_db_connection()

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

    conn = get_db_connection()

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

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cats WHERE id=?",
        (id,)
    )

    cat = cursor.fetchone()

    if cat is None:
        conn.close()
        return "Cat not found."

    cursor.execute(
        "UPDATE cats SET status='Found' WHERE id=?",
        (id,)
    )
    
    conn.commit()
    conn.close()

    return redirect("/cats")

@app.route("/")
def home():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cats")
    total_cats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cats WHERE status='Found'")
    found_cats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sightings")
    total_sightings = cursor.fetchone()[0]

    if total_cats == 0:
        recovery_rate = 0
    else:
        recovery_rate = round((found_cats / total_cats) * 100, 1)

    conn.close()

    return render_template(
        "index.html",
        total_cats=total_cats,
        found_cats=found_cats,
        total_sightings=total_sightings,
        recovery_rate=recovery_rate
    )
create_table()

if __name__ == "__main__":
    app.run(debug=True)