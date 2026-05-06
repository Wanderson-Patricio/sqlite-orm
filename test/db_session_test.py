import os

import pytest

from sqlite_orm.field import String, Integer, ID
from sqlite_orm.query_filter import Equals
from sqlite_orm.errors import NotFilteredQueryException, InvalidMethodAssociationException, MethodPrecedenceException
from sqlite_orm import DatabaseContextManager, DBSession, Model

class User(Model):
    __tablename__ = 'users'
    id = ID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)

database_name = 'test.db3'


def test_create_table():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)
        session = session.create_table()

        assert session.options.method == "CREATE_TABLE"

        session.execute()
        assert db.table_exists(User.__tablename__)

def test_select():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)

        session = session.select()

        assert session.options.method == "SELECT"

        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session.execute()
        
        assert "Must specify .all() or .first() before executing a SELECT query" in str(excinfo.value)

        users = session.all().execute()
        assert isinstance(users, list)

        user = session.select().first().execute()
        assert isinstance(user, tuple) or user is None


def test_insert():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)
        new_user = User(name="Alice", age=30)
        session = session.insert(new_user)

        assert session.options.method == "INSERT"

        session.execute()
        users = session.select().all().execute()
        assert len(users) == 1

        user = session.select().first().execute()
        assert isinstance(user, tuple)

        user = session.select().first().to_model().execute()
        assert isinstance(user, User)
        assert user.id == 1
        assert user.name == "Alice"
        assert user.age == 30


def test_update_error():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)
        session = session.update().set(name="Bob")
        with pytest.raises(NotFilteredQueryException) as excinfo:
            session.execute()
        assert "UPDATE queries must have at least one filter." in str(excinfo.value)

        session = DBSession(User, db)
        with pytest.raises(MethodPrecedenceException) as excinfo:
            session = session.update().where(id=Equals(1))
        
        assert "When on update method, the setters must be passed before the filters." in str(excinfo.value)

        session = DBSession(User, db)
        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session = session.update().limit(1)

        assert "The method 'limit' can only be used with SELECT queries." in str(excinfo.value)

def test_update():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)

        session = session.update()
        assert session.options.method == "UPDATE"

        session = session.set(name="Bob")
        assert session.options.update_set_clauses == ["name"]
        assert session.options.parameters == ["Bob"]

        session = session.where(id=Equals(1))
        assert len(session.options.filters) == 1

        filters = session.options.filters[0].__dict__.get('field_filters')
        assert filters is not None
        assert "id" in filters
        assert isinstance(filters["id"], Equals)
        assert filters["id"].query_symbol == "="
        assert filters["id"].value == 1
        assert session.options.parameters == ["Bob", 1]

        session.execute()
        user = session.select().first().to_model().execute()
        assert user == User(id=1, name="Bob", age=30)


def test_delete():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)
        session = session.delete().where(id=Equals(1))

        assert session.options.method == "DELETE"
        assert len(session.options.filters) == 1

        session.execute()
        users = session.select().first().where(id=Equals(1)).execute()
        assert users is None


def test_drop_table():
    with DatabaseContextManager(database_name) as db:
        session = DBSession(User, db)
        session = session.drop_table()

        assert session.options.method == "DROP_TABLE"

        session.execute()
        assert not db.table_exists(User.__tablename__)

    os.remove(database_name)