# BizEase WebSite Backend API

This is an internship project for the [tcu](https://www.linkedin.com/company/techies-collab-and-upskill-on-live-project/) 3.0 cohort

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

_to be updated_

## Building

_To be updated_

## Running unit tests

_To be updated_

## Running end-to-end tests

_To be updated_