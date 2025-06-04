# BizEase WebSite Backend API

This is an internship project for the [tcu](https://www.linkedin.com/company/techies-collab-and-upskill-on-live-project/) 3.0 cohort.

BizEase is a web app that helps businesses manage and optimize their sales processes, from inventory management to order management. 
It includes features like order tracking, pipeline management, reporting, and analytics. 
It aims to streamline sales activities, improve team collaboration, and ultimately boost sales performance. 

## Development

Before You get started, make sure you have Python 3.10, 3.11, or 3.12 installed and preferrably the latest release. 

These are the python versions that Django 5.2.1 supports.

**Create and activate a virtual environment**

Create the virtual environment
```bash
python -m venv <path/to/preferred/directory>
```

[Activate](https://docs.python.org/3/library/venv.html#how-venvs-work) the created virtual environment depending on the platform you are working on

**Install Dependencies inside the activated environment**

```bash
python -m pip install -r requirements.txt
```

**Move to proper path**

- Make sure you are at the root of the repo
- Navigate into the bizease folder from the root
- Run the commands below

**Apply migrations as needed**

```bash
python manage.py migrate
```

**Start the development server**

```bash
python manage.py runserver
```
Once the server is running, open your browser and navigate to `http://localhost:8000/` to view a web page without errors.

In case of any issue, please visit the official [django docs](https://docs.djangoproject.com/en/5.2/) or the official [python  docs](https://docs.python.org/3/) for help

## Code scaffolding

A Django project can contain multiple apps. Each Django app consists of a Python package that follows a certain convention 
and it usually handles a part of the django project e.g. Auth App. Django comes with a utility that automatically generates 
the basic directory structure of an app, so you can focus on writing code rather than creating directories.

To create your app, make sure you’re in the same directory as manage.py and type this command:
```bash
	python manage.py startapp polls
```

## Running unit tests

_To be updated_

## Running end-to-end tests

_To be updated_
