from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy
from .agent import Agent
from .script import Script
from .result import Result
from .deploy import Deploy