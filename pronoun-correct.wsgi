#flaskapp.wsgi
import sys
sys.path.insert(0, '/var/www/html/pronoun-correct')
sys.path.append('/home/ubuntu/pronoun-correct/lib/python3.7/site-packages')
from app import app as application
