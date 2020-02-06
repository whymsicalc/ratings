"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movie_list.html", movies=movies)


@app.route("/registration-form", methods=["GET"])
def show_reg_form():
    """Display registration form."""

    return render_template("registration_form.html")


@app.route("/registration-form", methods=["POST"])
def register_user():
    """Check if user exists and create user if user does not exist."""
    email = request.form.get("email")
    password = request.form.get("password")

    # Checking to see if user exists by checking email in users table
    if not User.query.filter_by(email=email).all():
        # Add user to users table by instantiating User object
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("User added!")
    else:
        flash("User already exists")

    return redirect("/")


@app.route("/login-page", methods=["GET"])
def show_login_form():
    """Display login form."""
    return render_template("login.html")


@app.route("/login-page", methods=["POST"])
def login_user():
    """Log in user if password matches."""
    email = request.form.get("email")
    password = request.form.get("password")
    # Find user instance from user table where email matches email from form
    user = User.query.filter_by(email=email).first()
    # Check if password matches to log them in
    if user.password == password:
        # Login stored in session
        session["user_id"] = user.user_id
        flash("Logged in")

        return redirect(f"/users/{user.user_id}")
    else:
        flash("Incorrect email/password")

        return redirect("/login-page")


@app.route("/logout")
def logout_user():
    """Log out a user"""

    # Delete session data to log out
    del session["user_id"]
    flash("Successfully logged out!")

    return redirect("/")


@app.route("/users/<int:user_id>")
def show_user_profile(user_id):
    """Show profile for given user."""
    user = User.query.filter_by(user_id=user_id).first()

    return render_template("user_profile.html", user=user)


@app.route("/movies/<int:movie_id>")
def show_movie_profile(movie_id):
    """Show profile for given movie."""

    # movie object given a movie_id
    movie = Movie.query.filter_by(movie_id=movie_id).first()

    # list of all rating objects for a given movie_id ordered by user_id
    sorted_ratings = Rating.query.filter_by(movie_id=movie_id).order_by('user_id').all()

    return render_template("movie_profile.html", movie=movie, ratings=sorted_ratings)


@app.route("/movies/<int:movie_id>", methods=["POST"])
def add_movie_rating(movie_id):
    """Add or update movie rating"""
    rating = request.form.get("rating")

    # Rating object from logged in user for movie on page
    user_rating_query = Rating.query.filter(Rating.user_id == session["user_id"], Rating.movie_id == movie_id).first()

    # Check to see if rating exists from logged in user
    if user_rating_query:
        # Update rating
        user_rating_query.score = rating
        db.session.commit()
        flash("Rating updated")

    else:
        # Since rating doesn't exist, add rating to ratings table
        user_rating = Rating(movie_id=movie_id, user_id=session["user_id"], score=rating)
        db.session.add(user_rating)
        db.session.commit()
        flash("Rating added")

    return redirect(f"/movies/{movie_id}")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
