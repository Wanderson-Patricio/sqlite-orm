from sqlite_orm.field import Field, String

import pytest

def test_create_field():
    class TestField(Field):
        def __init__(self):
            super().__init__(type='TEST')

        def __validate__(self, value):
            pass

    field = TestField()
    assert field is not None
    assert field.type == 'TEST'
    assert field.primary_key == False
    assert field.nullable == True
    assert field.unique == False


def test_must_raise_error_if_not_implemented_validate_method():
    with pytest.raises(TypeError) as exc_info:
        field = Field(type='TEST')
    assert "Can't instantiate abstract class Field without an implementation for abstract method '__validate__'" in str(exc_info.value)


def test_must_raise_error_if_dont_explicitly_set_kwargs():
    with pytest.raises(Exception) as exc_info:
        class TestField(Field):
            def __init__(self):
                super().__init__('TEST')

            def __validate__(self, value):
                raise NotImplementedError()
        
        field = TestField()
        
    assert "Field.__init__() takes 1 positional argument but 2 were given" in str(exc_info.value)
    

def test_string_field():
    with pytest.raises(TypeError) as exc_info:
        field = String(255)

    assert "String.__init__() takes 1 positional argument but 2 were given" in str(exc_info.value)
    
    s = String(max_length=255, primary_key=True, nullable=False, unique=True)
    assert s is not None
    assert s.type == 'VARCHAR'
    assert s.max_length == 255
    assert s.primary_key == True
    assert s.nullable == False
    assert s.unique == True