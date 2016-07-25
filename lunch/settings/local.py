from .base import *

SECRET_KEY = '4z7yqu324kl$_&&-zg=8k&en5_b7ao@lwg6z#w59+iwqjr4lfa'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(BASE_DIR), 'db.sqlite3'),
    }
}

