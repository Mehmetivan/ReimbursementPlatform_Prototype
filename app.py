from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret_key_123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------- DATABASE INIT ----------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            bank_details TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            receipt_file TEXT NOT NULL,
            comment TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(student_id) REFERENCES users(id)
        )
    """)

    # Insert sample users if they don't exist
    try:
        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                  ("student1@uni.com", "1234", "student"))
        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                  ("staff1@uni.com", "1234", "staff"))
    except:
        pass

    conn.commit()
    conn.close()


# ---------------------- LOGIN ROUTES ----------------------
@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=? AND password=? AND role=?", 
                  (email, password, role))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = role

            if role == "student":
                return redirect("/student_dashboard")
            else:
                return redirect("/staff_dashboard")

        return "Invalid credentials!"

    return render_template("login.html")


# ---------------------- STUDENT ROUTES ----------------------
@app.route("/student_dashboard")
def student_dashboard():
    if "role" not in session or session["role"] != "student":
        return redirect("/login")
    return render_template("student_dashboard.html")


@app.route("/submit_request", methods=["POST"])
def submit_request():
    if "role" not in session or session["role"] != "student":
        return redirect("/login")

    comment = request.form.get("comment")
    file = request.files["receipt"]

    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO requests (student_id, receipt_file, comment)
        VALUES (?, ?, ?)
    """, (session["user_id"], filename, comment))
    conn.commit()
    conn.close()

    return "Request submitted successfully!"


# ---------------------- STAFF ROUTES ----------------------
@app.route("/staff_dashboard")
def staff_dashboard():
    if "role" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT r.id, u.email, r.receipt_file, r.comment, r.status
        FROM requests r
        JOIN users u ON r.student_id = u.id
    """)
    requests_list = c.fetchall()
    conn.close()

    return render_template("staff_dashboard.html", requests=requests_list)


@app.route("/review_request/<int:req_id>/<string:action>")
def review_request(req_id, action):
    if "role" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    new_status = "Approved" if action == "approve" else "Rejected"
    c.execute("UPDATE requests SET status=? WHERE id=?", (new_status, req_id))
    conn.commit()
    conn.close()

    return redirect("/staff_dashboard")


# ---------------------- RUN ----------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
