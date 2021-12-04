from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
# from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps

import os
from dotenv import load_dotenv      # pip install python-dotenv

load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")       # read from .env file
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False,
                    use_ssl=False, base_url=None)

##CONNECT TO DB
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Base = declarative_base()

##CONFIGURE TABLES
# One to Many bidirectional relationship - User is parent, BlogPost is child. One user can have multiple blogposts
# https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(500), nullable=False)
    name = Column(String(100), nullable=False)
    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship('BlogPost', back_populates='author')
    user_comments = relationship('Comment', back_populates='comment_author')

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = Column(Integer, ForeignKey('users.id'))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship('User', back_populates='posts')       # the author property of BlogPost is now a User object
    # author = Column(String(250), nullable=False)
    title = Column(String(250), unique=True, nullable=False)
    subtitle = Column(String(250), nullable=False)
    date = Column(String(250), nullable=False)
    body = Column(Text, nullable=False)
    img_url = Column(String(250), nullable=False)
    blog_comments = relationship('Comment', back_populates='parent_post')       # BlogPost is parent for Comment


class Comment(db.Model):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    comment_author = relationship('User', back_populates='user_comments')
    post_id = Column(Integer, ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='blog_comments')
    text = Column(String(500), nullable=False)


# Create all the tables in the database
# db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    # print(current_user.id)
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user = User.query.filter_by(email=register_form.email.data).first()
        if user:
            flash("You've already Sign up with that email. Please login")
            return redirect(url_for('login'))
        else:
            hash_and_salted_password = generate_password_hash(
                register_form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User()
            new_user.email = register_form.email.data
            new_user.password = hash_and_salted_password
            new_user.name = register_form.name.data
            db.session.add(new_user)
            db.session.commit()
            # flash("You've registered successfully. Please login")
            # return redirect(url_for('login'))
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=register_form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if not user:
            flash("This email doesn't exist. Please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, login_form.password.data):
            flash("Incorrect Password. Please Try again")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


# A decorator is a function that wraps and replaces another function. Since the original function is replaced,
# you need to copy the original function’s information to the new function. Use functools.wraps() to handle this.

def admin_only(funct):
    @wraps(funct)  # copy the original function’s information to the new function
    def wrapper(*args, **kwargs):
        if current_user.id != 1:  # If id is not 1 then return abort with 403 error
            return abort(403)
        return funct(*args, **kwargs)  # Otherwise continue with the route function
    return wrapper


@app.route("/new-post", methods=['GET', 'POST'])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y"),
            # author_id=current_user.id,        # no need to supply id
            author=current_user
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body,
        author=current_user     # why do we need it. There is no such field in the form
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, current_user=current_user, is_edit=True)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    # comments = Comment.query.filter_by(post_id=post_id).all()
    # This is how two way relationships work. No need to query comments table as above
    # comments is a property of each blog post, you can treat it like a List.
    # comments = requested_post.blog_comments
    # Even this is not needed, since we are passing post as a parameter, no need to pass another parameter 'comments'
    # You can directly use post.blog_comments in post.html

    if form.validate_on_submit():
        if current_user.is_authenticated:
            # new_comment = Comment(
            #     author_id=current_user.id,
            #     post_id=post_id,
            #     text=form.comment.data
            # )
            # Tutorial Approach
            new_comment = Comment(
                text=form.comment.data,
                comment_author=current_user,
                parent_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            # No need for the below code
            # return redirect(url_for('show_post', post_id=post_id))
        else:
            flash('You need to log in or register to comment')
            return redirect(url_for('login'))
    return render_template("post.html", post=requested_post, form=form, current_user=current_user)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run()
    # app.run(host='0.0.0.0', port=5000)

