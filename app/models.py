from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5

# --- Schemas -> initial database sctructure

# loader function -> returns a user given the id
@login.user_loader  # the flask-login needs this function 
def load_user(id):
    return User.query.get(int(id))

followers = db.Table("followers", 
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"))
)
 
class User(UserMixin, db.Model): # a instance of the model object
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False) #VARCHAR
    email = db.Column(db.String(120), index=True, unique=True, nullable=False) #VARCHAR
    image = db.Column(db.String(20), nullable=False, default='default.jpg')
    password_hash = db.Column(db.String(128), nullable=True) #VARCHAR
    posts = db.relationship("Post", backref="author", lazy="dynamic") # lazy ->
    about_me = db.Column(db.String(140)) 
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship( # relationship many to many
        "User", secondary=followers, # User -> right side entity of the relation
        primaryjoin=(followers.c.follower_id == id), # condition linking the left
        # side entity (follower) with the association table
        secondaryjoin=(followers.c.followed_id == id),# condition linking the right
        # side entity (followed) with the association table
        backref=db.backref("followers", lazy="dynamic"), lazy="dynamic"
    )

    def __repr__(self): # redefining the representation
        return '<User {}>'.format(self.username)
        # >>> User(username='susan', email='susan@example.com')
        # <<< <User susan>

    def set_password(self, password): # replace pass with encrypted one 
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password): # returns true (equal passwords) or false (not equal)
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        avatar_id = 'identicon'
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d={avatar_id}&s={size}'

    #followers methods
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id # query to the relationship - "followeds by this user"
        ).count() > 0 # exists a follower with this id in the list

    def followed_posts(self): # see notes for explanation
        followed = Post.query.join( 
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc()) # combaining both

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    body = db.Column(db.String(140), index=True) 
    timestamp = db.Column(db.DateTime, index=True, nullable=False, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self): # redefining the representation
        return '<Post {}>'.format(self.body)

