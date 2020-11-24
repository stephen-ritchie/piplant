from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

import piplant.messages as messages
from piplant.models import db, User


auth = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.request_loader
def load_user_from_request(web_request):
    # Token is passed in as a parameter.
    auth_token = web_request.args.get('auth_token')
    if auth_token:
        resp = User.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            user = User.query.filter_by(id=resp).first()
            return user

    # Token is passed in the header
    auth_token = web_request.headers.get('Authorization')
    if auth_token:
        auth_token = auth_token.replace('Bearer', '', 1).strip()
        resp = User.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            user = User.query.filter_by(id=resp).first()
            return user

    return None


@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # remember = True if request.form.get('remember') else False
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed
        # password in database
        if not user or not check_password_hash(user.password, password):
            flash(messages.LOGIN_FAILED)
            # if user doesn't exist or password is wrong, reload the page
            return redirect(url_for('auth.login'))

        # if the above check passes, then we know the user has the right
        # credentials
        login_user(user, remember=remember)
        return redirect(url_for('home.landing'))

    return render_template('auth/login.html')


@auth.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # If a user is found, we want to redirect back to signup page so user
        # can try again
        if user:
            flash(messages.ACCOUNT_WITH_EMAIL_ALREADY_EXISTS)
            return redirect(url_for('auth.register'))

        # create new user with the form data. Hash the password so plaintext
        # version isn't saved. add the new user to the database
        db.session.add(
            User(
                email=email,
                name=name,
                password=generate_password_hash(password, method='sha256')
            )
        )
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
