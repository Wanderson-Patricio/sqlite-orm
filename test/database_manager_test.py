import os

from sqlite_orm import DatabaseContextManager

database_name = "test.db3"

def test_database_creation():
    assert not os.path.exists(database_name)
    with DatabaseContextManager(database_name) as conn:
        assert os.path.exists(database_name)

def test_database_connection():
    with DatabaseContextManager(database_name) as conn:
        assert conn is not None

def test_database_cleanup():
    if os.path.exists(database_name):
        os.remove(database_name)
        assert not os.path.exists(database_name)