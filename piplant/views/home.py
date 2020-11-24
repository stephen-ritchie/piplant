from flask import Blueprint, render_template
from flask_login import current_user, login_required

from piplant.lib import get_devices, get_users

home = Blueprint('home', __name__)


@home.route('/', methods=['GET'])
@login_required
def landing():
    devices = get_devices(current_user.id)
    users = get_users()
    return render_template('index.html', devices=devices, users=users)
