# -*- coding: utf-8 -*-

from flask.ext.wtf import Form, BooleanField, TextField, PasswordField, validators


class RegistrationForm(Form):
    username = TextField(u'Nazwa użytkownika', [validators.Length(min=4, max=25)], id="username")
    email = TextField(u'Adres email', [validators.Length(min=6, max=35)], id="email")
    password = PasswordField(u'Nowe hasło', [
        validators.Required(),
        validators.EqualTo('confirm', message='Hasła muszą być takie same')
    ], id="password")
    confirm = PasswordField(u'Powtórz hasło', id="confirm")

class LoginForm(Form):
    username = TextField(u'Nazwa użytkownika', [validators.Length(min=4, max=25)], id="username")
    password = PasswordField(u'Hasło', [
        validators.Required(),
    ], id="password")