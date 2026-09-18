from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from datetime import datetime
from functools import wraps
import os
import secrets


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "classnest-secret-key-change-later"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///classnest.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "uploads"
)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


db = SQLAlchemy(app)


ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "jpg",
    "jpeg",
    "png",
    "zip"
}


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    classrooms = db.relationship(
        "Classroom",
        backref="teacher",
        lazy=True
    )

    enrollments = db.relationship(
        "Enrollment",
        backref="student",
        lazy=True
    )

    submissions = db.relationship(
        "Submission",
        backref="student",
        lazy=True
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )


class Classroom(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    section = db.Column(
        db.String(50)
    )

    description = db.Column(
        db.Text
    )

    class_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    assignments = db.relationship(
        "Assignment",
        backref="classroom",
        lazy=True,
        cascade="all, delete-orphan"
    )

    announcements = db.relationship(
        "Announcement",
        backref="classroom",
        lazy=True,
        cascade="all, delete-orphan"
    )

    enrollments = db.relationship(
        "Enrollment",
        backref="classroom",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Enrollment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    classroom_id = db.Column(
        db.Integer,
        db.ForeignKey("classroom.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "classroom_id",
            "student_id",
            name="unique_enrollment"
        ),
    )


class Assignment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    classroom_id = db.Column(
        db.Integer,
        db.ForeignKey("classroom.id"),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    due_date = db.Column(
        db.DateTime
    )

    max_marks = db.Column(
        db.Integer,
        default=100
    )

    attachment = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    submissions = db.relationship(
        "Submission",
        backref="assignment",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Submission(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("assignment.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    file_path = db.Column(
        db.String(255)
    )

    submitted_at = db.Column(
        db.DateTime
    )

    marks = db.Column(
        db.Integer
    )

    feedback = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(30),
        default="Not Submitted"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "assignment_id",
            "student_id",
            name="unique_submission"
        ),
    )


class Announcement(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    classroom_id = db.Column(
        db.Integer,
        db.ForeignKey("classroom.id"),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(User, user_id)


def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("user_id"):

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return decorated_function


def teacher_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        user = get_current_user()

        if not user or user.role != "teacher":

            flash(
                "Teacher access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function


def student_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        user = get_current_user()

        if not user or user.role != "student":

            flash(
                "Student access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def generate_class_code():

    while True:

        code = secrets.token_hex(4).upper()

        existing = Classroom.query.filter_by(
            class_code=code
        ).first()

        if not existing:

            return code


def student_in_classroom(
    student_id,
    classroom_id
):

    return Enrollment.query.filter_by(
        student_id=student_id,
        classroom_id=classroom_id
    ).first() is not None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html",
        user=get_current_user()
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        role = request.form.get(
            "role"
        )

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if role not in ["teacher", "student"]:

            flash(
                "Please select a valid role.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        user = User(
            name=name,
            email=email,
            role=role
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            session.clear()

            session["user_id"] = user.id
            session["name"] = user.name
            session["role"] = user.role

            flash(
                f"Welcome to ClassNest, {user.name}!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user = get_current_user()

    if user.role == "teacher":

        classrooms = Classroom.query.filter_by(
            teacher_id=user.id
        ).order_by(
            Classroom.created_at.desc()
        ).all()

        classroom_ids = [
            classroom.id
            for classroom in classrooms
        ]

        assignments = 0
        student_count = 0

        if classroom_ids:

            assignments = Assignment.query.filter(
                Assignment.classroom_id.in_(
                    classroom_ids
                )
            ).count()

            student_count = Enrollment.query.filter(
                Enrollment.classroom_id.in_(
                    classroom_ids
                )
            ).count()

        return render_template(
            "dashboard.html",
            user=user,
            classrooms=classrooms,
            assignments=assignments,
            student_count=student_count
        )

    else:

        enrollments = Enrollment.query.filter_by(
            student_id=user.id
        ).order_by(
            Enrollment.joined_at.desc()
        ).all()

        classrooms = [
            enrollment.classroom
            for enrollment in enrollments
        ]

        classroom_ids = [
            classroom.id
            for classroom in classrooms
        ]

        recent_assignments = []

        if classroom_ids:

            recent_assignments = Assignment.query.filter(
                Assignment.classroom_id.in_(
                    classroom_ids
                )
            ).order_by(
                Assignment.created_at.desc()
            ).limit(5).all()

        return render_template(
            "dashboard.html",
            user=user,
            classrooms=classrooms,
            recent_assignments=recent_assignments
        )


# =========================================================
# CREATE CLASSROOM
# =========================================================

@app.route(
    "/create-classroom",
    methods=["GET", "POST"]
)
@teacher_required
def create_classroom():

    if request.method == "POST":

        name = request.form.get(
            "name", ""
        ).strip()

        subject = request.form.get(
            "subject", ""
        ).strip()

        section = request.form.get(
            "section", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        if not name or not subject:

            flash(
                "Class name and subject are required.",
                "danger"
            )

            return redirect(
                url_for("create_classroom")
            )

        classroom = Classroom(
            name=name,
            subject=subject,
            section=section,
            description=description,
            class_code=generate_class_code(),
            teacher_id=session["user_id"]
        )

        db.session.add(classroom)
        db.session.commit()

        flash(
            "Classroom created successfully!",
            "success"
        )

        return redirect(
            url_for(
                "classroom",
                classroom_id=classroom.id
            )
        )

    return render_template(
        "classroom.html",
        create_mode=True
    )


# =========================================================
# VIEW CLASSROOM
# =========================================================

@app.route(
    "/classroom/<int:classroom_id>"
)
@login_required
def classroom(classroom_id):

    user = get_current_user()

    classroom = db.session.get(
        Classroom,
        classroom_id
    )

    if not classroom:

        flash(
            "Classroom not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if user.role == "teacher":

        if classroom.teacher_id != user.id:

            flash(
                "You do not have access to this classroom.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

    else:

        if not student_in_classroom(
            user.id,
            classroom.id
        ):

            flash(
                "You are not enrolled in this classroom.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

    return render_template(
        "classroom.html",
        classroom=classroom,
        user=user
    )


# =========================================================
# JOIN CLASSROOM
# =========================================================

@app.route(
    "/join-classroom",
    methods=["POST"]
)
@student_required
def join_classroom():

    code = request.form.get(
        "class_code", ""
    ).strip().upper()

    if not code:

        flash(
            "Please enter a class code.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    classroom = Classroom.query.filter_by(
        class_code=code
    ).first()

    if not classroom:

        flash(
            "Invalid class code.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    existing = Enrollment.query.filter_by(
        classroom_id=classroom.id,
        student_id=session["user_id"]
    ).first()

    if existing:

        flash(
            "You are already enrolled in this class.",
            "info"
        )

        return redirect(
            url_for("dashboard")
        )

    enrollment = Enrollment(
        classroom_id=classroom.id,
        student_id=session["user_id"]
    )

    db.session.add(enrollment)
    db.session.commit()

    flash(
        f"You joined {classroom.name} successfully!",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# CREATE ASSIGNMENT
# =========================================================

@app.route(
    "/classroom/<int:classroom_id>/create-assignment",
    methods=["GET", "POST"]
)
@teacher_required
def create_assignment(classroom_id):

    classroom = db.session.get(
        Classroom,
        classroom_id
    )

    if not classroom:

        flash(
            "Classroom not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if classroom.teacher_id != session["user_id"]:

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        title = request.form.get(
            "title", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        due_date_text = request.form.get(
            "due_date", ""
        )

        max_marks_text = request.form.get(
            "max_marks", "100"
        )

        file = request.files.get(
            "attachment"
        )

        if not title:

            flash(
                "Assignment title is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "create_assignment",
                    classroom_id=classroom_id
                )
            )

        try:

            max_marks = int(max_marks_text)

            if max_marks <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Marks must be a positive number.",
                "danger"
            )

            return redirect(
                url_for(
                    "create_assignment",
                    classroom_id=classroom_id
                )
            )

        due_date = None

        if due_date_text:

            try:

                due_date = datetime.strptime(
                    due_date_text,
                    "%Y-%m-%dT%H:%M"
                )

            except ValueError:

                flash(
                    "Invalid due date.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "create_assignment",
                        classroom_id=classroom_id
                    )
                )

        filename = None

        if file and file.filename:

            if not allowed_file(file.filename):

                flash(
                    "This file type is not allowed.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "create_assignment",
                        classroom_id=classroom_id
                    )
                )

            safe_name = secure_filename(
                file.filename
            )

            unique_name = (
                secrets.token_hex(8)
                + "_"
                + safe_name
            )

            os.makedirs(
                app.config["UPLOAD_FOLDER"],
                exist_ok=True
            )

            file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    unique_name
                )
            )

            filename = unique_name

        assignment = Assignment(
            classroom_id=classroom.id,
            teacher_id=session["user_id"],
            title=title,
            description=description,
            due_date=due_date,
            max_marks=max_marks,
            attachment=filename
        )

        db.session.add(assignment)
        db.session.commit()

        flash(
            "Assignment created successfully!",
            "success"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment.id
            )
        )

    return render_template(
        "assignment.html",
        classroom=classroom,
        create_mode=True
    )


# =========================================================
# VIEW ASSIGNMENT
# =========================================================

@app.route(
    "/assignment/<int:assignment_id>"
)
@login_required
def assignment(assignment_id):

    user = get_current_user()

    assignment_obj = db.session.get(
        Assignment,
        assignment_id
    )

    if not assignment_obj:

        flash(
            "Assignment not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    classroom = assignment_obj.classroom

    if user.role == "teacher":

        if classroom.teacher_id != user.id:

            flash(
                "You do not have access to this assignment.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        submission = None

    else:

        if not student_in_classroom(
            user.id,
            classroom.id
        ):

            flash(
                "You are not enrolled in this classroom.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        submission = Submission.query.filter_by(
            assignment_id=assignment_obj.id,
            student_id=user.id
        ).first()

    return render_template(
        "assignment.html",
        assignment=assignment_obj,
        classroom=classroom,
        submission=submission,
        user=user
    )


# =========================================================
# SUBMIT ASSIGNMENT
# =========================================================

@app.route(
    "/assignment/<int:assignment_id>/submit",
    methods=["POST"]
)
@student_required
def submit_assignment(assignment_id):

    user = get_current_user()

    assignment_obj = db.session.get(
        Assignment,
        assignment_id
    )

    if not assignment_obj:

        flash(
            "Assignment not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if not student_in_classroom(
        user.id,
        assignment_obj.classroom_id
    ):

        flash(
            "You are not enrolled in this class.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    file = request.files.get(
        "submission_file"
    )

    if not file or not file.filename:

        flash(
            "Please select a file.",
            "danger"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment_id
            )
        )

    if not allowed_file(file.filename):

        flash(
            "This file type is not allowed.",
            "danger"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment_id
            )
        )

    safe_name = secure_filename(
        file.filename
    )

    unique_name = (
        secrets.token_hex(8)
        + "_"
        + safe_name
    )

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    file.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_name
        )
    )

    submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=user.id
    ).first()

    if submission:

        if submission.file_path:

            old_file = os.path.join(
                app.config["UPLOAD_FOLDER"],
                submission.file_path
            )

            if os.path.exists(old_file):

                os.remove(old_file)

        submission.file_path = unique_name
        submission.submitted_at = datetime.utcnow()
        submission.status = "Submitted"

    else:

        submission = Submission(
            assignment_id=assignment_id,
            student_id=user.id,
            file_path=unique_name,
            submitted_at=datetime.utcnow(),
            status="Submitted"
        )

        db.session.add(submission)

    db.session.commit()

    flash(
        "Assignment submitted successfully!",
        "success"
    )

    return redirect(
        url_for(
            "assignment",
            assignment_id=assignment_id
        )
    )


# =========================================================
# GRADE SUBMISSION
# =========================================================

@app.route(
    "/submission/<int:submission_id>/grade",
    methods=["GET", "POST"]
)
@teacher_required
def grade_submission(submission_id):

    submission = db.session.get(
        Submission,
        submission_id
    )

    if not submission:

        flash(
            "Submission not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    assignment_obj = submission.assignment

    classroom = assignment_obj.classroom

    if classroom.teacher_id != session["user_id"]:

        flash(
            "You do not have permission to grade this submission.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        marks_text = request.form.get(
            "marks", ""
        ).strip()

        feedback = request.form.get(
            "feedback", ""
        ).strip()

        try:

            marks = int(marks_text)

        except ValueError:

            flash(
                "Marks must be a number.",
                "danger"
            )

            return redirect(
                url_for(
                    "grade_submission",
                    submission_id=submission_id
                )
            )

        if marks < 0 or marks > assignment_obj.max_marks:

            flash(
                f"Marks must be between 0 and {assignment_obj.max_marks}.",
                "danger"
            )

            return redirect(
                url_for(
                    "grade_submission",
                    submission_id=submission_id
                )
            )

        submission.marks = marks
        submission.feedback = feedback
        submission.status = "Graded"

        db.session.commit()

        flash(
            "Submission graded successfully!",
            "success"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment_obj.id
            )
        )

    return render_template(
        "assignment.html",
        assignment=assignment_obj,
        classroom=classroom,
        grading_submission=submission,
        user=get_current_user()
    )


# =========================================================
# CREATE ANNOUNCEMENT
# =========================================================

@app.route(
    "/classroom/<int:classroom_id>/announcement",
    methods=["POST"]
)
@teacher_required
def create_announcement(classroom_id):

    classroom = db.session.get(
        Classroom,
        classroom_id
    )

    if not classroom:

        flash(
            "Classroom not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if classroom.teacher_id != session["user_id"]:

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    content = request.form.get(
        "content", ""
    ).strip()

    if not content:

        flash(
            "Announcement cannot be empty.",
            "danger"
        )

        return redirect(
            url_for(
                "classroom",
                classroom_id=classroom_id
            )
        )

    announcement = Announcement(
        classroom_id=classroom_id,
        teacher_id=session["user_id"],
        content=content
    )

    db.session.add(announcement)
    db.session.commit()

    flash(
        "Announcement posted!",
        "success"
    )

    return redirect(
        url_for(
            "classroom",
            classroom_id=classroom_id
        )
    )


# =========================================================
# DOWNLOAD ASSIGNMENT FILE
# =========================================================

@app.route(
    "/assignment/<int:assignment_id>/download"
)
@login_required
def download_assignment_file(assignment_id):

    assignment_obj = db.session.get(
        Assignment,
        assignment_id
    )

    if not assignment_obj:

        flash(
            "Assignment not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = get_current_user()

    if user.role == "teacher":

        allowed = (
            assignment_obj.classroom.teacher_id
            == user.id
        )

    else:

        allowed = student_in_classroom(
            user.id,
            assignment_obj.classroom_id
        )

    if not allowed:

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if not assignment_obj.attachment:

        flash(
            "No attachment found.",
            "warning"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment_id
            )
        )

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        assignment_obj.attachment,
        as_attachment=True
    )


# =========================================================
# DOWNLOAD SUBMISSION FILE
# =========================================================

@app.route(
    "/submission/<int:submission_id>/download"
)
@login_required
def download_submission_file(submission_id):

    submission = db.session.get(
        Submission,
        submission_id
    )

    if not submission:

        flash(
            "Submission not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = get_current_user()

    assignment_obj = submission.assignment

    if user.role == "teacher":

        allowed = (
            assignment_obj.classroom.teacher_id
            == user.id
        )

    else:

        allowed = (
            submission.student_id == user.id
        )

    if not allowed:

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if not submission.file_path:

        flash(
            "No submission file found.",
            "warning"
        )

        return redirect(
            url_for(
                "assignment",
                assignment_id=assignment_obj.id
            )
        )

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        submission.file_path,
        as_attachment=True
    )


# =========================================================
# ERROR: FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 16 MB.",
        "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# CREATE DATABASE AND RUN APP
# =========================================================

if __name__ == "__main__":

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    with app.app_context():

        db.create_all()

    print("")
    print("======================================")
    print("       CLASSNEST IS STARTING")
    print("======================================")
    print("Open: http://127.0.0.1:5000")
    print("======================================")
    print("")

    app.run(
        debug=True
    )