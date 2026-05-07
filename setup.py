from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sqlite_orm',
    version='1.0.1',
    packages=find_packages(include=['sqlite_orm', 'sqlite_orm.*']),
    install_requires=[],
    description='A simple ORM for SQLite databases in Python.',
    author='Wanderson Faustino Patricio',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Wanderson-Patricio/sqlite-orm',
    license='MIT',
    author_email='wanderfapat@gmail.com',
    keywords='sqlite orm python database'
)