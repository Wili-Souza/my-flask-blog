import logging
from logging.handlers import SMTPHandler
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment

# creating app that is being exported
app = Flask(__name__) # special variable -> name of the module
app.config.from_object(Config) # passing our object as the configuration
db = SQLAlchemy(app) # creating alchemy instance
migrate = Migrate(app, db) #creating migration intance
login = LoginManager(app) #initializing flask-login
login.login_view = "login" # <- function name | for @login_requried
moment = Moment(app)

# geting the routes from the routes file to execute them
from app import routes, models, errors

if not app.debug:
    if app.config['MAIL_SERVER']: # se for configurado informações de email
        auth = None
        if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
            auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        secure = None
        if app.config["MAIL_USE_TLS"]:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            fromaddr="no-reply@" + app.config["MAIL_SERVER"],
            toaddrs=app.config["ADMINS"], subject="FlaskBlog Failure",
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)