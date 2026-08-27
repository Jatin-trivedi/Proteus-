"""
Models package – defines database instance and exports all models.
"""

from flask_sqlalchemy import SQLAlchemy

# Create the database instance
db = SQLAlchemy()

# Import models (after db is defined to avoid circular imports)
from .agent import Agent
from .script import Script
from .result import Result
from .deploy import Deploy

# Export everything
__all__ = ['db', 'Agent', 'Script', 'Result', 'Deploy']