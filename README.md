### Basic requirements

- Python 3.6

### Create a virtual environment

To keep dependencies in a single place, create virtual environment
```shell
$ python -m venv django-app
```

Now activate the newly created environment
```shell
$ . django-app/bin/activate
# You will see the activated env on the left-rand side of your shell. something like this
(django-app) <username> $  
```

Install Django
```shell
$ pip install django
```

Run the migrations
```shell
$ python manage.py migrate
```

Create a super user for the admin interface
```shell
$ python manage.py createsuperuser
```

Run the server
```shell
$ python manage.py runserver
```


