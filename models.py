# -*- coding: utf-8 -*-
import datetime

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    pw_hash = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80))

    def __init__(self, name, email, pw_hash):
        self.name = name
        self.email = email
        self.pw_hash = pw_hash

    @classmethod
    def by_id(cls, uid):
        return cls.query.filter_by(id=uid).one()

    @classmethod
    def by_name(cls, name):
        u = cls.query.filter_by(name=name).first()
        return u


post_tags = db.Table('post_tags', db.metadata,
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User',
        backref=db.backref('posts'))

    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))
    page = db.relationship('Page',
        backref=db.backref('posts'))

    tags_id = db.Column(db.Integer, db.ForeignKey('tags.id'))
    tags = db.relationship('Tag', secondary=post_tags,
        backref=db.backref('posts'))


    def __init__(self, text, user=None, pub_date=None):
        self.text = text
        if not pub_date:
            pub_date = datetime.datetime.utcnow()
        self.user = user
        self.pub_date = pub_date

    @classmethod
    def by_id(cls, id):
        return cls.query.filter_by(id=id).one()


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, tag):
        self.tag = tag

    @classmethod
    def by_id(cls, id):
        return cls.query.filter_by(id=id).one()

    @classmethod
    def by_name(cls, name):
        u = cls.query.filter_by(tag=name).first()
        return u

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, url):
        self.url = url

    @classmethod
    def by_id(cls, id):
        return cls.query.filter_by(id=id).one()

    @classmethod
    def by_name(cls, name):
        u = cls.query.filter_by(url=name).first()
        return u