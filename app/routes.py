import os
import secrets
from PIL import Image # from pillow module
from app import app, db
from app.models import User, Post
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from flask import abort, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, UpdateAccountForm, EmptyForm, PostForm
from datetime import datetime

# --- Views

# adding the routes to the app using decorators
@app.route("/", methods=["POST", "GET"]) # both routes take you to home page
@app.route("/home", methods=["POST", "GET"])
@login_required
def home():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been published!", "success")
        return redirect(url_for("home"))
    posts = current_user.followed_posts()
    #pagination
    page = request.args.get('page', 1, type=int) # type=int converts in int | 1 is the default initial page if none
    posts = current_user.followed_posts().paginate( 
        # current page, number of posts, False -> don't show error when page is empty
        page, app.config["POSTS_PER_PAGE"], False  
    )
    next_url = url_for("home", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("home", page=posts.prev_num) if posts.has_prev else None
    return render_template("home.html", title="Home", posts=posts.items,
                           form=form, next_url=next_url, prev_url=prev_url)

@app.route("/about")
def about():
    user = {"username": "Miguel"}
    return render_template("about.html", title="About", user=user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    
    form = RegistrationForm() # a flask form object
    if form.validate_on_submit(): # method from flask object
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # flash(message, category)
        flash(f"Your account has been created!", "success")
        return redirect(url_for("login"))
    return render_template('register.html', title="register", form=form) # sending our form

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: # already logged in 
        return redirect(url_for("home"))

    form = LoginForm() # a flask form object
    if form.validate_on_submit(): # if form is validated
        user = User.query.filter_by(email=form.email.data).first() # gets user by email
        if user is None or not user.check_password(form.password.data): # if user don't exist or password is wrong
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))
        # for correct infos:
        login_user(user, remember=form.remember.data) # log user in -> put user as current_user
        flash("Successfully logged in!", "success")
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "": # if not defined or is a absolute url (has a domain)
            next_page = url_for("home")
        return redirect(next_page)
    return render_template('login.html', title="Login", form=form) # sending our form

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # name and extension of the file path
    _, f_ext = os.path.splitext(form_picture.filename)
    # picture file name
    picture_fn = random_hex + f_ext
    # concatenating the whole new path
    picture_path = os.path.join(app.root_path, 'static', 'profile_pics', picture_fn)

    # resize the picture before save
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm(current_user.username)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Data successfully updated.", "success")
        return redirect(url_for('account'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about_me.data = current_user.about_me
    image_file = url_for('static', filename="profile_pics/" + current_user.image)

    return render_template("account.html", title="Account", image_file=image_file, form=form)

@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = Post.query.filter_by(author=user).paginate(
        page, app.config["POSTS_PER_PAGE"], False
    )
    next_url = url_for("user", username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for("user", username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template(
        "user.html", 
        title="User", 
        user=user, 
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form
    )

@app.before_request  #executed before any view function
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow() # current_user doesn't require db.session.add()
        db.session.commit()

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f"User {username} not found!", "danger")
            return redirect(url_for("home"))
        if user == current_user:
            flash("You cannot unfollow you own profile.", "danger")
            return redirect(url_for("home", username=username))
        current_user.unfollow(user) # unfollows
        db.session.commit() # save in database
        flash(f"You are not following {username} anymore.", "success")
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("home"))

@app.route("/explore")
@login_required
def explore():
    page = request.args.get('page', 1, type=int) 
    posts = Post.query.order_by(Post.timestamp.desc()).paginate( # instead of all() we'll use paginate
        page, app.config["POSTS_PER_PAGE"], False  
    )
    next_url = url_for("explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("explore", page=posts.prev_num) if posts.has_prev else None
    return render_template("home.html", title="Explore", posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

@app.route("/post/<post_id>/update", methods=["POST", "GET"])
@login_required
def EditPost(post_id):
    form=PostForm()
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
            abort(403)  # unforbidden route
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.content.data
        db.session.commit()
        flash("Your post has been updated.", "success")
        return redirect(url_for("EditPost", post_id=post_id))
    elif request.method =="GET":
        form.title.data = post.title
        form.content.data = post.body
    

    return render_template("edit_post.html", title="Update Post", form=form, post=post)

@app.route("/post/<post_id>/delete", methods=["POST"])
@login_required
def DeletePost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
            abort(403)  # unforbidden route
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been successfully deleted.", "success")
    return redirect(url_for("home"))
    
