import pytest

from sqlite_orm.model import Model
from sqlite_orm.field import String, Integer, ID

class User(Model):
    __tablename__ = 'users'
    id = ID()
    name = String(max_length=100, nullable=False)
    age = Integer(nullable=False)

def test_create_user():
    user = User(id=1, name="Alice", age=30)

    assert user.id == 1
    assert isinstance(user.id, int)

    assert user.name == "Alice"
    assert isinstance(user.name, str)

    assert user.age == 30
    assert isinstance(user.age, int)
    
    assert repr(user) == "<User (id: 1, name: Alice, age: 30)>"

    with pytest.raises(AttributeError) as exc_info:
        user.field

    assert "'User' object has no attribute 'field'" in str(exc_info.value)