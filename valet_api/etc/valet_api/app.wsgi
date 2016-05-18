# /var/www/valet/app.wsgi
from pecan.deploy import deploy

application = deploy('/var/www/valet/config.py')
