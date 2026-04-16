from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "super_secret_key_123"


# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- LANDING ----------------
@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                (email, username, hashed_password)
            )
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="User already exists")
        finally:
            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session["user"] = user["email"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["username"])


# ---------------- TEMPLATES PAGE ----------------
@app.route("/templates")
def templates():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("templates.html")


# ---------------- CREATE PORTFOLIO (MULTI-STEP FORM) ----------------
@app.route("/create_portfolio", methods=["GET", "POST"])
def create_portfolio():
    if "user" not in session:
        return redirect(url_for("login"))

    template = request.args.get("template")

    # When form is submitted
    if request.method == "POST":
        data = request.form.to_dict()
        selected_template = request.form.get("selected_template")

        # Render selected template dynamically
        return render_template(
            f"templates_portfolio/{selected_template}.html",
            data=data
        )

    # When opening form
    return render_template("create_portfolio.html", template=template)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)