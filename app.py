from flask import Flask, render_template, request, redirect, session, send_file
from datetime import datetime
import os
import uuid
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = 'cloudproject123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(500))
    share_token = db.Column(db.String(100))
    upload_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    user_id = db.Column(db.Integer)

# Create Database
with app.app_context():
    db.create_all()

# Home Page
@app.route("/")
def home():
    return render_template("home.html")

# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered"

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    files = File.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "dashboard.html",
        username=session["username"],
        files=files
    )

#upload_route
@app.route("/upload", methods=["POST"])
def upload():

    if "user_id" not in session:
        return redirect("/login")

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return redirect("/dashboard")

    filepath = os.path.join(
        "uploads",
        uploaded_file.filename
    )

    uploaded_file.save(filepath)

    share_token = str(uuid.uuid4())[:8]

    new_file = File(
        filename=uploaded_file.filename,
        filepath=filepath,
        share_token=share_token,
        user_id=session["user_id"]
    )

    db.session.add(new_file)
    db.session.commit()

    return redirect("/dashboard")

#download_route
@app.route("/download/<int:file_id>")
def download(file_id):

    file = File.query.get_or_404(file_id)

    return send_file(
        file.filepath,
        as_attachment=True
    )

#delete_route
@app.route("/delete/<int:file_id>")
def delete_file(file_id):

    if "user_id" not in session:
        return redirect("/login")

    file = File.query.get_or_404(file_id)

    if os.path.exists(file.filepath):
        os.remove(file.filepath)

    db.session.delete(file)
    db.session.commit()

    return redirect("/dashboard")

#share_link_route
@app.route("/get-share-link/<int:file_id>")
def get_share_link(file_id):

    file = File.query.get_or_404(file_id)

    share_url = f"http://127.0.0.1:5000/share/{file.share_token}"

    return f"""
    <!DOCTYPE html>
    <html>

    <head>

        <title>Share Link</title>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

    </head>

    <body class="bg-light">

    <div class="container mt-5">

        <div class="card shadow p-4">

            <h2 class="mb-4">
                Share Link
            </h2>

            <input
                type="text"
                value="{share_url}"
                id="shareLink"
                class="form-control mb-3"
                readonly
            >

            <button
                class="btn btn-success"
                onclick="copyLink()">

                Copy Link

            </button>

            <br><br>

            <a href="/dashboard"
               class="btn btn-primary">

                Back to Dashboard

            </a>

        </div>

    </div>

    <script>

    function copyLink() {{

        let copyText =
        document.getElementById("shareLink");

        copyText.select();

        copyText.setSelectionRange(
            0,
            99999
        );

        navigator.clipboard.writeText(
            copyText.value
        );

        alert(
            "Link Copied Successfully!"
        );

    }}

    </script>

    </body>

    </html>
    """

# share_route
@app.route("/share/<token>")
def share_file(token):

    file = File.query.filter_by(
        share_token=token
    ).first()

    if not file:
        return "File Not Found"

    return send_file(
        file.filepath,
        as_attachment=True
    )

# Shared Links Page
@app.route("/shared-links")
def shared_links():

    if "user_id" not in session:
        return redirect("/login")

    files = File.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "shared_links.html",
        files=files
    )

# My Files Page
@app.route("/my-files")
def my_files():

    if "user_id" not in session:
        return redirect("/login")

    files = File.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "my_files.html",
        username=session["username"],
        files=files
    )


# Profile Page
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(
        session["user_id"]
    )

    return render_template(
        "profile.html",
        user=user
    )

# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)