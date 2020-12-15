import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

import piplant.lib as lib
import piplant.messages as messages

user = Blueprint('user', __name__)


@user.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
def about(user_id):
    _user = lib.get_user(user_id)
    if _user is None:
        flash(messages.USER_NOT_FOUND)
        return redirect(url_for("home.landing"))

    if request.method == 'POST':
        # TODO: Schema validation
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        try:
            lib.update_user(_user.id, name=name, email=email, phone=phone)
            return redirect(url_for("home.landing"))
        except Exception as err:
            logging.error(str(err))
            flash(str(err))

    return render_template('user/about.html', user=_user)
