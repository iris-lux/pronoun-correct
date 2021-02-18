#flaskapp.wsgi
import sys
sys.path.insert(0, '/var/www/html/pronoun-correct')
sys.path.append('/var/www/html/pronoun-correct/lib/python3.8/site-packages')
from app import app as application
