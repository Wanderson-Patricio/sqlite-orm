from typing import Dict

from .field import Field
from .errors import ValidationError

class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):
        if name == "Model":
            return super().__new__(mcs, name, bases, attrs)

        __tablename__ = attrs.pop('__tablename__', name.lower())
        fields = {}

        # Varre os atributos procurando por instâncias de Field
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key # Informa ao campo o seu próprio nome
                fields[key] = value

        attrs['__tablename__'] = __tablename__
        attrs['_fields'] = fields

        return super().__new__(mcs, name, bases, attrs)

class HasAttributeVericator:
    def __init__(self, model: "Model", field_name: str):
        self.model = model
        self.field_name = field_name

    def verifiy(self, value):
        if not hasattr(self.model, self.field_name):
            raise AttributeError(f"'{self.model.__class__.__name__}' object has no attribute '{self.field_name}'.")
        setattr(self.model, self.field_name, value)


class HasAllNonNullableFieldsVericator:
    def __init__(self, model: "Model"):
        self.model = model

    def verifiy(self, values: Dict = None):
        values = values or {}
        for field_name, field in self.model._fields.items():
            if not field.nullable and values.get(field_name) is None:
                raise ValidationError(f"Field '{field_name}' of '{self.model.__class__.__name__}' cannot be null.")


class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        HasAllNonNullableFieldsVericator(self).verifiy(kwargs)

        for key, value in kwargs.items():
            HasAttributeVericator(self, key).verifiy(value)
            setattr(self, key, value)

    def __repr__(self):
        field_values = ", ".join(f"{field}: {getattr(self, field)}" for field in self._fields)
        return f"<{self.__class__.__name__} ({field_values})>"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Model):
            return False
        return all(getattr(self, field) == getattr(other, field) for field in self._fields)