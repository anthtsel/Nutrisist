from setuptools import setup, find_packages

setup(
    name="health_diet_plan",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'Flask-WTF',
        'Flask-Migrate',
        'psycopg2-binary',
        'python-dotenv',
        'Werkzeug',
        'email-validator',
        'garminconnect',
        'requests',
        'pymongo',
    ],
) 