# /var/www/allegro/app.wsgi
from pecan.deploy import deploy

application = deploy('/var/www/allegro/config.py')
