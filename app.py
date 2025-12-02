from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------------------
# DATABASE INITIALIZATION
# --------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            email TEXT PRIMARY KEY,
            name TEXT,
            iban TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            filename TEXT,
            comment TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # Seed default users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('student@uni.ro', '123', 'student')")
        c.execute("INSERT INTO users VALUES ('staff@uni.ro', '123', 'staff')")

    conn.commit()
    conn.close()

init_db()


# --------------------------
# ROUTES
# --------------------------
@app.route("/")
def index():
    return redirect("/login")


# --------------------------
# LOGIN
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT email, role FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["email"] = user[0]
            session["role"] = user[1]

            return redirect("/student" if user[1] == "student" else "/staff")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# --------------------------
# STUDENT DASHBOARD
# --------------------------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")

    email = session["email"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT name, iban FROM students WHERE email=?", (email,))
    student = c.fetchone()

    c.execute("SELECT id, filename, comment, status FROM requests WHERE student_email=?", (email,))
    reqs = c.fetchall()

    conn.close()

    return render_template("student_dashboard.html", student=student, requests=reqs)


@app.route("/submit_info", methods=["POST"])
def submit_info():
    name = request.form["name"]
    iban = request.form["iban"]
    email = session["email"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("REPLACE INTO students VALUES (?, ?, ?)", (email, name, iban))
    conn.commit()
    conn.close()

    return redirect("/student")


@app.route("/submit_request", methods=["POST"])
def submit_request():
    file = request.files["receipt"]
    comment = request.form.get("comment", "")
    filename = file.filename
    file.save(os.path.join("static/uploads", filename))

    email = session["email"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO requests (student_email, filename, comment) VALUES (?, ?, ?)",
              (email, filename, comment))
    conn.commit()
    conn.close()

    return redirect("/student")


# --------------------------
# STAFF DASHBOARD (REQUESTS)
# --------------------------
@app.route("/staff")
def staff_dashboard():
    if session.get("role") != "staff":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    reqs = c.fetchall()
    conn.close()

    return render_template("staff_dashboard.html", requests=reqs)


@app.route("/review_request/<int:id>/<action>")
def review_request(id, action):
    if session.get("role") != "staff":
        return redirect("/login")

    status = "Approved" if action == "approve" else "Rejected"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE requests SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

    return redirect("/staff")


# --------------------------
# STAFF — MANAGE STUDENTS
# --------------------------
@app.route("/manage_students")
def manage_students():
    if session.get("role") != "staff":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE role='student'")
    students = c.fetchall()
    conn.close()

    return render_template("manage_students.html", students=students)


@app.route("/add_student", methods=["POST"])
def add_student():
    if session.get("role") != "staff":
        return redirect("/login")

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, 'student')",
              (email, password))
    conn.commit()
    conn.close()

    return redirect("/manage_students")


@app.route("/delete_student/<email>")
def delete_student(email):
    if session.get("role") != "staff":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email=?", (email,))
    c.execute("DELETE FROM requests WHERE student_email=?", (email,))
    conn.commit()
    conn.close()

    return redirect("/manage_students")


@app.route("/update_student", methods=["POST"])
def update_student():
    if session.get("role") != "staff":
        return redirect("/login")

    email = request.form["email"]
    new_password = request.form["new_password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
    conn.commit()
    conn.close()

    return redirect("/manage_students")


# --------------------------
# RUN SERVER
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
