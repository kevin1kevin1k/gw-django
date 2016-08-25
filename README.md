# Guess What [![Live Demo](https://img.shields.io/badge/demo-online-green.svg)](http://learn.iis.sinica.edu.tw:9181)

A web interactive answer guessing game in Chinese Traditional.

---

## Installation

#### Clone this repo

```sh
git clone https://github.com/kevin1kevin1k/gw-django
```

#### Files needed

- resultSimple.csv
- eHowNet-utf8.csv
- ASBC.txt
- cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin

*Put them into /resources directory.*

#### Requirements

- Python 2.* (2.7 recommended)
- django
- django-crispy-forms
- numpy
- sklearn
- scipy
- simplejson
- bs4
- gensim

You can directly `pip install` them, or install them in virtual environment with the following steps:

1. Install the virtualenv package and create venv

    ```sh
    pip install virtualenv
    virtualenv venv
    ```

2. Activate the virtual environment

    If you are using Windows:
    ```sh
    venv\Scripts\activate
    ```

    For other users (Linux, Mac, etc.):
    ```sh
    source venv/bin/activate
    ```

3. Now you can `pip install` them in the virtual environment.  

*To exit the virtual environment, just `deactivate`.*

#### Running locally

```sh
cd gw-django
python manage.py runserver
```

Then check out `http://localhost:8000` on your web browser.

*In fact, the IP address and port can be specified.  
For example,*
```sh
python manage.py runserver 1.2.3.4:5678
```

*The default ip/port is 127.0.0.1:8000.*
