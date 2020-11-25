import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from piplant.views.api import schemas
import piplant.lib as lib

user = Blueprint('user', __name__)


@user.route('/user', methods=['GET', 'POST'])
@login_required
def about():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        try:
            lib.update_user(current_user.id, name=name, email=email, phone=phone)
            return redirect(url_for("home.landing"))
        except Exception as err:
            logging.error(str(err))
            flash(str(err))

    return render_template('user/about.html', user=current_user)
