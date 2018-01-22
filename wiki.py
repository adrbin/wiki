# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib
import urllib2
import random
import logging
import datetime
from xml.dom import minidom
from string import letters
from hashlib import md5

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, _app_ctx_stack, send_from_directory, Markup, jsonify
from flaskext.bcrypt import Bcrypt

from models import *
from forms import *

# configuration
DEBUG = True
SECRET_KEY = 'development key'
_basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'wiki.db')

# create the application
app = Flask(__name__)
app.config.from_object(__name__)
db.app = app
db.init_app(app)
bcrypt = Bcrypt(app)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return username and USER_RE.match(username)


PASS_RE = re.compile(r"^.{3,20}$")


def valid_password(password):
    return password and PASS_RE.match(password)


EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_email(email):
    return not email or EMAIL_RE.match(email)


# LINK_RE = re.compile(ur'#\{([a-zA-Z0-9%_ ąĄęĘóÓłŁżŻźźŹćĆ]+)\}', re.UNICODE)
LINK_RE = re.compile(ur'#\{([\w0-9%_ ]+)\}', re.UNICODE)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_field = request.form['search'].strip().lower()
    print search_field
    if request.method == 'POST' and search_field:
        return redirect(url_for('page', page_url=search_field))
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter_by(id=session['user_id']).first()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))
    form = RegistrationForm(request.form)
    errors = []
    if request.method == 'POST' and form.validate():
        if User.by_name(form.username.data):
            errors.append(u"Ta nazwa użytkownika jest już wykorzystywana")
        else:
            # print form.password.data
            user = User(form.username.data, form.email.data,
                        bcrypt.generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            flash(u'Dziękujemy za rejestrację')
            return redirect(url_for('index'))
    return render_template('register.html', form=form, errors=errors)


@app.route('/')
def index():
    pages = db.session.query(Page).join(
        Post).order_by(Post.pub_date.desc())[:10]
    return render_template('index.html', pages=pages,
                           urllib=urllib)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    errors = []
    if request.method == 'POST' and form.validate():
        user = User.by_name(form.username.data)
        # print user.pw_hash
        if user and bcrypt.check_password_hash(user.pw_hash, form.password.data):
            session['user_id'] = user.id
            flash(u'Dziękujemy za zalogowanie')
            return redirect(url_for('index'))
        else:
            errors.append(u'Nazwa użytkownika oraz hasło się nie zgadzają')
    return render_template('login.html', form=form, errors=errors)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash(u'Zostałeś wylogowany')
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/wiki/<page_url>')
def page(page_url):
    page_url = page_url.strip().lower()
    p = Page.query.filter_by(url=page_url).first()
    if not p:
        flash(u"Ta strona jeszcze nie istnieje. Możesz ją utworzyć!")
        return redirect(url_for('edit', page_url=page_url))
    # post = p.posts.query.order_by("pub_date").first()
    post = db.session.query(Post).join(Page).filter(
        Page.url == page_url).order_by(Post.pub_date.desc()).first()
    text = convert_links(post.text)
    return render_template('page.html', post=post, title=page_url.capitalize(), url=page_url, text=text)


@app.route('/wiki/<page_url>/<id>')
def post(page_url, id):
    page_url = page_url.strip().lower()
    p = Page.query.filter_by(url=page_url).first()
    if not p:
        flash(u"Ta strona jeszcze nie istnieje. Możesz ją utworzyć!")
        return redirect(url_for('edit', page_url=page_url))
    # post = p.posts.query.order_by("pub_date").first()
    post = db.session.query(Post).filter_by(id=id).first()
    text = convert_links(post.text)
    return render_template('post.html', post=post, title=page_url.capitalize(), url=page_url, text=text)


def convert_links(text):
    text = unicode(Markup.escape(text))
    text = text.replace('\n', '<br>')
    text = LINK_RE.sub(ur'<a href="/wiki/\g<1>">\g<1></a>', text)
    return text


@app.route('/tags/<tag_url>')
def tags(tag_url):
    tag_url = tag_url.strip().lower()
    t = Tag.query.filter_by(tag=tag_url).first()
    if not t:
        flash(u"Nie ma tekiego tagu.")
        return redirect(url_for('index'))
    posts = t.posts[-10:]
    return render_template('tags.html', posts=reversed(posts), title=tag_url.capitalize())


@app.route('/users/<user_url>')
def users(user_url):
    user_url = user_url.strip().lower()
    u = User.query.filter_by(name=user_url).first()
    if not u:
        flash(u"Nie ma tekiego użytkownika")
        return redirect(url_for('index'))
    posts = u.posts[-10:]
    return render_template('users.html', posts=reversed(posts), title=user_url.capitalize(),
                           url=user_url, urllib=urllib, user=u)


@app.route('/wiki/<page_url>/edit', methods=["GET", "POST"])
def edit(page_url):
    page_url = page_url.strip().lower()
    errors = []
    if not g.user:
        flash(u'Musisz być zalogowanym, aby móc edytować tą stronę')
        return redirect(url_for('login'))
    if request.method == "POST":
        if not request.form['text'].strip():
            errors.append(u'Tekst nie może być pusty')
        else:
            post = Post(request.form['text'])
            p = Page.query.filter_by(url=page_url).first()
            if not p:
                p = Page(page_url)
            post.page = p
            tags = request.form['tags'].strip().split()
            if tags:
                for tag in tags:
                    t = Tag.by_name(tag)
                    if not t:
                        t = Tag(tag)
                    post.tags.append(t)
            post.user = g.user
            db.session.add(post)
            db.session.commit()
            flash(u'Twój post został dodany')
            return redirect(url_for('page', page_url=page_url))
    post = db.session.query(Post).join(Page).filter(
        Page.url == page_url).order_by(Post.pub_date.desc()).first()
    text = ""
    tags = ""
    if post:
        text = post.text
        tags = " ".join([tag.tag for tag in post.tags])
    return render_template('edit.html', page_url=page_url, errors=errors, title=page_url.capitalize(),
                           url=page_url, text=text, re=re, tags=tags)


@app.route('/wiki/<page_url>/history')
def history(page_url):
    page_url = page_url.strip().lower()
    p = Page.query.filter_by(url=page_url).first()
    if not p:
        return redirect(url_for('edit', page_url=page_url))
    posts = db.session.query(Post).join(Page).filter(
        Page.url == page_url).order_by(Post.pub_date.desc()).all()
    return render_template('history.html', page=p, posts=posts,
                           title=page_url.capitalize(), url=page_url)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/_user_check')
def user_check():
    username = request.args.get('username', '', type=str)
    if User.by_name(username):
        result = True
    else:
        result = False
    return jsonify(result=result, username=username)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


app.jinja_env.filters['gravatar'] = gravatar_url
app.jinja_env.filters['convert_links'] = convert_links


if __name__ == '__main__':
    db.create_all()
    app.run()
