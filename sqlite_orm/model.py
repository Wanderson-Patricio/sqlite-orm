from typing import Dict

from .field import Field
from .errors import ValidationError

class ModelMeta(type):
    """
    Metaclass for defining models.

    This metaclass processes class attributes to identify fields and sets up
    metadata for the model, such as the table name and fields.

    Attributes:
        __tablename__ (str): The name of the database table associated with the model.
        _fields (Dict[str, Field]): A dictionary mapping field names to their Field instances.
    """
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
    """
    Verifies if a model has a specific attribute.

    Attributes:
        model (Model): The model instance to verify.
        field_name (str): The name of the field to check.
    """
    def __init__(self, model: "Model", field_name: str):
        self.model = model
        self.field_name = field_name

    def verifiy(self, value):
        """
        Checks if the model has the specified attribute and sets its value.

        Args:
            value: The value to set for the attribute.

        Raises:
            AttributeError: If the model does not have the specified attribute.
        """
        if not hasattr(self.model, self.field_name):
            raise AttributeError(f"'{self.model.__class__.__name__}' object has no attribute '{self.field_name}'.")
        setattr(self.model, self.field_name, value)


class HasAllNonNullableFieldsVericator:
    """
    Verifies that all non-nullable fields in a model have values.

    Attributes:
        model (Model): The model instance to verify.
    """
    def __init__(self, model: "Model"):
        self.model = model

    def verifiy(self, values: Dict = None):
        """
        Ensures all non-nullable fields have values.

        Args:
            values (Dict, optional): A dictionary of field values. Defaults to None.

        Raises:
            ValidationError: If a non-nullable field is missing a value.
        """
        values = values or {}
        for field_name, field in self.model._fields.items():
            if not field.nullable and values.get(field_name) is None:
                raise ValidationError(f"Field '{field_name}' of '{self.model.__class__.__name__}' cannot be null.")


class Model(metaclass=ModelMeta):
    """
    Base class for all models.

    This class provides the foundation for defining models with fields and
    ensures that all required fields are validated during initialization.

    Attributes:
        _fields (Dict[str, Field]): A dictionary mapping field names to their Field instances.
        __tablename__ (str): The name of the database table associated with the model.
    """
    def __init__(self, **kwargs):
        """
        Initializes a model instance with the given field values.

        Args:
            **kwargs: Field values to initialize the model.

        Raises:
            ValidationError: If a non-nullable field is missing a value.
            AttributeError: If an invalid field is provided.
        """
        HasAllNonNullableFieldsVericator(self).verifiy(kwargs)

        for key, value in kwargs.items():
            HasAttributeVericator(self, key).verifiy(value)
            setattr(self, key, value)

    def __repr__(self):
        """
        Returns a string representation of the model instance.

        Returns:
            str: A string representation of the model with its field values.
        """
        field_values = ", ".join(f"{field}: {getattr(self, field)}" for field in self._fields)
        return f"<{self.__class__.__name__} ({field_values})>"
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two model instances are equal based on their field values.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if not isinstance(other, Model):
            return False
        return all(getattr(self, field) == getattr(other, field) for field in self._fields)