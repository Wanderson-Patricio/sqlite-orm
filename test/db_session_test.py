import os
import pytest

from sqlite_orm.field import String, Integer, IntegerID, UUID
from sqlite_orm.errors import NotFilteredQueryException, InvalidMethodAssociationException, MethodPrecedenceException
from sqlite_orm.selector import Distinct, Count, Max, Min
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
        assert isinstance(user, dict) or user is None

        user = session.select().first().to_model().execute()
        assert isinstance(user, User)
        assert user.id == 1
        assert user.name == "Alice"
        assert user.age == 30


def test_integer_id_update_error():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(User)
        session = session.update().set(User.name=="Bob")
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

        session = session.set(User.name=="Bob")
        assert session.options.update_set_clauses == [f"name"]
        assert session.options.parameters == ["Bob"]

        session = session.where(User.id == 1)
        assert len(session.options.filters) == 1

        expression = session.options.filters[0]
        assert expression.operator == "="
        assert expression.left == f"{User.__tablename__}.id"
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
        assert isinstance(user, dict) or user is None

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
        session = session.update().set(User.name=="Bob")
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

        session = session.set(User.name=="Bob")
        assert session.options.update_set_clauses == ["name"]
        assert session.options.parameters == ["Bob"]

        session = session.where(UserUUID.id == get_user_id())
        assert len(session.options.filters) == 1

        expression = session.options.filters[0]
        assert expression.operator == "="
        assert expression.left == f"{User.__tablename__}.id"
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


################################################################################
################################################################################
############### Teste com Selectors ############################################
################################################################################
################################################################################

class UserSelector(Model):
    __tablename__ = 'users'
    id = IntegerID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


def test_selectors_count():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserSelector)
        session.create_table().execute()

        session.insert(UserSelector(name="Alice", age=22)).execute()
        session.insert(UserSelector(name="Bob", age=30)).execute()
        session.insert(UserSelector(name="Carol", age=40)).execute()
        session.insert(UserSelector(name="Alice", age=39)).execute()

        users = (
            session
            .select(Count(UserSelector).As("user_count"))
            .first()
            .to_model()
            .execute()
        )

        assert users.user_count == 4


def test_selectors_distinct():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserSelector)

        users = (
            session
            .select(Distinct(UserSelector.name).As("distinct_names"))
            .all()
            .to_model()
            .execute()
        )

        distinct_names = {user.distinct_names for user in users}
        assert distinct_names == {"Alice", "Bob", "Carol"}


def test_selectors_max_min():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserSelector)

        max_age_user = (
            session
            .select(Max(UserSelector.age).As("max_age"))
            .first()
            .to_model()
            .execute()
        )

        min_age_user = (
            session
            .select(Min(UserSelector.age).As("min_age"))
            .first()
            .to_model()
            .execute()
        )

        assert max_age_user.max_age == 40
        assert min_age_user.min_age == 22


    os.remove(database_name)


################################################################################
################################################################################
############### Teste com Retorno do método Insert #############################
################################################################################
################################################################################

class UserInsertIntegerID(Model):
    __tablename__ = 'users_id'
    id = IntegerID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


class UserInsertUUID(Model):
    __tablename__ = 'users_uuid'
    id = UUID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)

def test_insert_return_integer_id():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserInsertIntegerID)
        session.create_table().execute()

        new_user = UserInsertIntegerID(name="Alice", age=30)
        user_id = session.insert(new_user).execute()

        assert isinstance(user_id, int)
        assert user_id == 1


def test_insert_return_uuid():
    def is_valid_uuid(uuid_string):
        return (
            isinstance(uuid_string, str) and
            len(uuid_string) == 36 and 
            uuid_string.count('-') == 4 and 
            all(c in "0123456789abcdef-" for c in uuid_string.lower())
        )

    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserInsertUUID)
        session.create_table().execute()

        new_user = UserInsertUUID(name="Alice", age=30)
        user_id = session.insert(new_user).execute()

        assert is_valid_uuid(user_id)

    os.remove(database_name)


################################################################################
################################################################################
############### Teste com Order_by (ASC e DESC ) ###############################
################################################################################
################################################################################

class UserInsertOrdeByIntegerID(Model):
    __tablename__ = 'users_id'
    id = IntegerID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


class UserInsertOrdeByUUID(Model):
    __tablename__ = 'users_uuid'
    id = UUID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


def test_order_by_integer_id():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserInsertOrdeByIntegerID)
        session.create_table().execute()

        session.insert(UserInsertOrdeByIntegerID(name="Alice", age=30)).execute()
        session.insert(UserInsertOrdeByIntegerID(name="Bob", age=25)).execute()
        session.insert(UserInsertOrdeByIntegerID(name="Charlie", age=35)).execute()

        users_asc = (
            session
            .select()
            .all()
            .order_by(UserInsertOrdeByIntegerID.age, ascending=True)
            .to_model()
            .execute()
        )

        users_desc = (
            session
            .select()
            .all()
            .order_by(UserInsertOrdeByIntegerID.age, ascending=False)
            .to_model()
            .execute()
        )

        assert [user.age for user in users_asc] == [25, 30, 35]
        assert [user.age for user in users_desc] == [35, 30, 25]


def test_order_by_uuid():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserInsertOrdeByUUID)
        session.create_table().execute()

        session.insert(UserInsertOrdeByUUID(name="Alice", age=30)).execute()
        session.insert(UserInsertOrdeByUUID(name="Bob", age=25)).execute()
        session.insert(UserInsertOrdeByUUID(name="Charlie", age=35)).execute()

        users_asc = (
            session
            .select()
            .all()
            .order_by(UserInsertOrdeByUUID.age, ascending=True)
            .to_model()
            .execute()
        )

        users_desc = (
            session
            .select()
            .all()
            .order_by(UserInsertOrdeByUUID.age, ascending=False)
            .to_model()
            .execute()
        )

        assert [user.age for user in users_asc] == [25, 30, 35]
        assert [user.age for user in users_desc] == [35, 30, 25]

    os.remove(database_name)


################################################################################
################################################################################
############### Teste com Group_by #############################################
################################################################################
################################################################################

class UserGroupBy(Model):
    __tablename__ = 'users_groupby'
    id = IntegerID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)


def test_group_by_count():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserGroupBy)
        session.create_table().execute()

        session.insert(UserGroupBy(name="Alice", age=22)).execute()
        session.insert(UserGroupBy(name="Alice", age=30)).execute()
        session.insert(UserGroupBy(name="Bob", age=25)).execute()
        session.insert(UserGroupBy(name="Carol", age=40)).execute()
        session.insert(UserGroupBy(name="Carol", age=35)).execute()

        results = (
            session
            .select(UserGroupBy.name.As("name"), Count(UserGroupBy).As("total"))
            .all()
            .group_by(UserGroupBy.name)
            .to_model()
            .execute()
        )

        counts = {r.name: r.total for r in results}
        assert counts == {"Alice": 2, "Bob": 1, "Carol": 2}


def test_group_by_max_age():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserGroupBy)

        results = (
            session
            .select(UserGroupBy.name.As("name"), Max(UserGroupBy.age).As("max_age"))
            .all()
            .group_by(UserGroupBy.name)
            .to_model()
            .execute()
        )

        ages = {r.name: r.max_age for r in results}
        assert ages == {"Alice": 30, "Bob": 25, "Carol": 40}


def test_group_by_with_filter():
    with DatabaseContextManager(database_name) as db:
        session = db.get_session(UserGroupBy)

        results = (
            session
            .select(UserGroupBy.name.As("name"), Count(UserGroupBy).As("total"))
            .all()
            .where(UserGroupBy.age > 24)
            .group_by(UserGroupBy.name)
            .to_model()
            .execute()
        )

        counts = {r.name: r.total for r in results}
        assert counts == {"Alice": 1, "Bob": 1, "Carol": 2}

    os.remove(database_name)


################################################################################
################################################################################
############### Teste com JOIN #################################################
################################################################################
################################################################################

from sqlite_orm.field import ForeignKey


class Author(Model):
    __tablename__ = 'authors'
    id = IntegerID()
    name = String(max_length=100, nullable=False)


class Book(Model):
    __tablename__ = 'books'
    id = IntegerID()
    title = String(max_length=200, nullable=False)
    author_id = Integer(
        nullable=False,
        foreign_key=ForeignKey(reference_model=Author, reference_field=Author.id),
    )


def test_join_select_fields():
    with DatabaseContextManager(database_name) as db:
        db.get_session(Author).create_table().execute()
        db.get_session(Book).create_table().execute()

        session_a = db.get_session(Author)
        aid1 = session_a.insert(Author(name="Tolkien")).execute()
        aid2 = session_a.insert(Author(name="Martin")).execute()

        session_b = db.get_session(Book)
        session_b.insert(Book(title="The Hobbit", author_id=aid1)).execute()
        session_b.insert(Book(title="LOTR", author_id=aid1)).execute()
        session_b.insert(Book(title="ASOIAF", author_id=aid2)).execute()

        results = (
            db.get_session(Author)
            .select(Author.name.As("author"), Book.title.As("title"))
            .all()
            .join(Book)
            .on(Author.id == Book.author_id)
            .to_model()
            .execute()
        )

        assert len(results) == 3
        titles = {r.title for r in results}
        assert titles == {"The Hobbit", "LOTR", "ASOIAF"}


def test_join_with_where_filter():
    with DatabaseContextManager(database_name) as db:
        results = (
            db.get_session(Author)
            .select(Author.name.As("author"), Book.title.As("title"))
            .all()
            .join(Book)
            .on(Author.id == Book.author_id)
            .where(Author.name == "Tolkien")
            .to_model()
            .execute()
        )

        assert len(results) == 2
        assert all(r.author == "Tolkien" for r in results)


def test_join_with_count_group_by():
    with DatabaseContextManager(database_name) as db:
        results = (
            db.get_session(Author)
            .select(Author.name.As("author"), Count(Book).As("total"))
            .all()
            .join(Book)
            .on(Author.id == Book.author_id)
            .group_by(Author.name)
            .to_model()
            .execute()
        )

        counts = {r.author: r.total for r in results}
        assert counts == {"Tolkien": 2, "Martin": 1}


def test_join_with_order_by():
    with DatabaseContextManager(database_name) as db:
        results = (
            db.get_session(Author)
            .select(Author.name.As("author"), Book.title.As("title"))
            .all()
            .join(Book)
            .on(Author.id == Book.author_id)
            .order_by(Book.title, ascending=True)
            .to_model()
            .execute()
        )

        titles = [r.title for r in results]
        assert titles == sorted(titles)

    os.remove(database_name)