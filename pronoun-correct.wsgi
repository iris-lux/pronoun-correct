#flaskapp.wsgi
import sys
sys.path.insert(0, '/var/www/html/pronoun-correct')

from app import app as application
