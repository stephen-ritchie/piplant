#!/usr/bin/env python

from distutils.core import setup

setup(
    name='piplant',
    author='Stephen Ritchie',
    author_email='stephenfritchie@gmail.com',
    url='https://github.com/stephen-ritchie/PiPlant',
    packages=['piplant'],
    python_requires='>=3',
    install_requires=[
        'Flask',
        'flask_login',
        'flask-sqlalchemy',
        'sqlalchemy',
        'marshmallow',
        'werkzeug',
        'requests',
        'pyjwt'
    ]
)
