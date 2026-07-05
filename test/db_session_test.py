import os

import pytest

from sqlite_orm.field import String, Integer, IntegerID, UUID
from sqlite_orm.errors import NotFilteredQueryException, InvalidMethodAssociationException, MethodPrecedenceException
from sqlite_orm import DatabaseContextManager, Model

class User(Model):
    __tablename__ = 'users'
    id = IntegerID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)

database_name = 'test.db3'


def test_integer_id_create_table():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
        session = session.create_table()

        assert session.options.method == "CREATE_TABLE"

        session.execute()
        assert db.table_exists(User.__tablename__)

def test_integer_id_select():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)

        session = session.select()

        assert session.options.method == "SELECT"

        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session.execute()
        
        assert "Must specify .all() or .first() before executing a SELECT query" in str(excinfo.value)

        users = session.all().execute()
        assert isinstance(users, list)

        user = session.select().first().execute()
        assert isinstance(user, tuple) or user is None


def test_integer_id_insert():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
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


def test_integer_id_update_error():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
        session = session.update().set(name="Bob")
        with pytest.raises(NotFilteredQueryException) as excinfo:
            session.execute()
        assert "UPDATE queries must have at least one filter." in str(excinfo.value)

        session = db.get_session(User)
        with pytest.raises(MethodPrecedenceException) as excinfo:
            session = session.update().where(User.id == 1)
        
        assert "When on update method, the setters must be passed before the filters." in str(excinfo.value)

        session = db.get_session(User)
        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session = session.update().limit(1)

        assert "The method 'limit' can only be used with SELECT queries." in str(excinfo.value)

def test_integer_id_update():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)

        session = session.update()
        assert session.options.method == "UPDATE"

        session = session.set(name="Bob")
        assert session.options.update_set_clauses == ["name"]
        assert session.options.parameters == ["Bob"]

        session = session.where(User.id == 1)
        assert len(session.options.filters) == 1

        expression = session.options.filters[0]
        assert expression.operator == "="
        assert expression.left == "id"
        assert expression.right == 1
        assert session.options.parameters == ["Bob", 1]

        session.execute()
        user = session.select().first().to_model().execute()
        assert user == User(id=1, name="Bob", age=30)


def test_integer_id_delete():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
        session = session.delete().where(User.id == 1)

        assert session.options.method == "DELETE"
        assert len(session.options.filters) == 1

        session.execute()
        users = session.select().first().where(User.id == 1).execute()
        assert users is None


def test_integer_id_select_with_expression_composition():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)

        session.insert(User(name="Alice", age=22)).execute()
        session.insert(User(name="Bob", age=30)).execute()
        session.insert(User(name="Carol", age=40)).execute()

        users = (
            session
            .select()
            .all()
            .where((User.age > 25) & ((User.name == "Bob") | (User.name == "Carol")))
            .to_model()
            .execute()
        )

        assert len(users) == 2
        assert {u.name for u in users} == {"Bob", "Carol"}


def test_integer_id_drop_table():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
        session = session.drop_table()

        assert session.options.method == "DROP_TABLE"

        session.execute()
        assert not db.table_exists(User.__tablename__)

    os.remove(database_name)



################################################################################
################################################################################
################################################################################
################################################################################


class UserUUID(Model):
    __tablename__ = 'users'
    id = UUID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


def test_uuid_create_table():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        session = session.create_table()

        assert session.options.method == "CREATE_TABLE"

        session.execute()
        assert db.table_exists(User.__tablename__)


def test_uuid_select():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)

        session = session.select()

        assert session.options.method == "SELECT"

        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session.execute()
        
        assert "Must specify .all() or .first() before executing a SELECT query" in str(excinfo.value)

        users = session.all().execute()
        assert isinstance(users, list)

        user = session.select().first().execute()
        assert isinstance(user, tuple) or user is None


def get_user_id():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        user = session.select().first().to_model().execute()
        return user.id if user else None

def test_uuid_insert():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        new_user = UserUUID(name="Alice", age=30)

        print(f"new_user: {new_user}")
        session = session.insert(new_user)

        assert session.options.method == "INSERT"

        session.execute()
        users = session.select().all().execute()
        assert len(users) == 1

        user = session.select().first().execute()
        assert isinstance(user, tuple)

        user = session.select().first().to_model().execute()
        assert isinstance(user, UserUUID)
        assert user.id is not None
        assert user.id == get_user_id()
        assert isinstance(user.id, str)
        assert user.name == "Alice"
        assert user.age == 30


def test_uuid_update_error():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        session = session.update().set(name="Bob")
        with pytest.raises(NotFilteredQueryException) as excinfo:
            session.execute()
        assert "UPDATE queries must have at least one filter." in str(excinfo.value)

        session = db.get_session(UserUUID)
        with pytest.raises(MethodPrecedenceException) as excinfo:
            session = session.update().where(UserUUID.id == get_user_id())
        
        assert "When on update method, the setters must be passed before the filters." in str(excinfo.value)

        session = db.get_session(UserUUID)
        with pytest.raises(InvalidMethodAssociationException) as excinfo:
            session = session.update().limit(1)

        assert "The method 'limit' can only be used with SELECT queries." in str(excinfo.value)

def test_uuid_update():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)

        session = session.update()
        assert session.options.method == "UPDATE"

        session = session.set(name="Bob")
        assert session.options.update_set_clauses == ["name"]
        assert session.options.parameters == ["Bob"]

        session = session.where(UserUUID.id == get_user_id())
        assert len(session.options.filters) == 1

        expression = session.options.filters[0]
        assert expression.operator == "="
        assert expression.left == "id"
        assert expression.right == get_user_id()
        assert session.options.parameters == ["Bob", get_user_id()]

        session.execute()
        user = session.select().first().to_model().execute()
        assert user == UserUUID(id=get_user_id(), name="Bob", age=30)


def test_uuid_delete():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        session = session.delete().where(UserUUID.id == get_user_id())

        assert session.options.method == "DELETE"
        assert len(session.options.filters) == 1

        session.execute()
        users = session.select().first().where(UserUUID.id == get_user_id()).execute()
        assert users is None


def test_uuid_select_with_expression_composition():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)

        session.insert(UserUUID(name="Alice", age=22)).execute()
        session.insert(UserUUID(name="Bob", age=30)).execute()
        session.insert(UserUUID(name="Carol", age=40)).execute()

        users = (
            session
            .select()
            .all()
            .where((UserUUID.age > 25) & ((UserUUID.name == "Bob") | (UserUUID.name == "Carol")))
            .to_model()
            .execute()
        )

        assert len(users) == 2
        assert {u.name for u in users} == {"Bob", "Carol"}


def test_uuid_drop_table():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserUUID)
        session = session.drop_table()

        assert session.options.method == "DROP_TABLE"

        session.execute()
        assert not db.table_exists(User.__tablename__)

    os.remove(database_name)
