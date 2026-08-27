from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable

from .expression import Expression

@dataclass(frozen=True)
class ForeignKey:
    reference_model: Any
    reference_field: Any
    on_delete: str = "CASCADE"
    on_update: str = "SET NULL"

    def __post_init__(self):
        from .model import Model

        table = self.reference_model
        if isinstance(table, type) and issubclass(table, Model):
            return

        if not isinstance(table, Model):
            raise TypeError(
                "ForeignKey.reference_table must be a Model class or an instance of a Model class "
                "(got {type(table).__name__})"
            )
        

    @property
    def reference_table_name(self):
        from .model import Model

        model = self.reference_model
        if isinstance(model, type) and issubclass(model, Model):
            return model.__tablename__

        return model.__class__.__tablename__  # Retorna o nome da classe do modelo se for uma instância


    @property
    def reference_field_name(self):
        field = self.reference_field
        if hasattr(field, "name"):
            return field.name
        return str(field)  # Retorna o nome do campo se for uma instância de Field, caso contrário, converte para string


class Field(ABC):
    """
    Base class for all field types in the ORM.

    Besides validation and descriptor behavior, Field overloads comparison
    operators to build Expression objects that can be passed to DBSession.where.
    """

    def __init__(self,
                *,
                type: str, 
                primary_key: bool = False, 
                nullable: bool = True, 
                unique: bool = False,
                foreign_key: ForeignKey = None,
                default: Any = None
            ) -> None:
        
        self.name = None
        self.__type = type
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.nullable = nullable
        self.unique = unique
        self.default = default

        self.parent_model = None  # This will be set when the field is added to a model class

    def __str__(self):
        return ("<Field "
                f"name={self.name} "
                f"type={self.__type} "
                f"primary_key={self.primary_key} "
                f"nullable={self.nullable} "
                f"unique={self.unique} "
                f"foreign_key={self.foreign_key}> "
                f"default={self.default}> "
                f"parent_model={self.parent_model.__name__ if self.parent_model else '-'}"
                ">"
            )

    def __repr__(self):
        return str(self)

    @property
    def type(self):
        return self.__type
    
    # O Descriptor Protocol: controla o acesso ao dado na instância
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        # Aqui você pode adicionar validações estilo Pydantic!
        value = self.__validate__(value)
        instance.__dict__[self.name] = value

    @abstractmethod
    def __validate__(self, value):
        if value is None:
            if self.default is not None:
                value = self.default() if callable(self.default) else self.default
                
            else:
                if not self.nullable:
                    raise ValueError(f"Field '{self.name}' cannot be None")
        
        return value

    def __left_expression_input(self) -> str:
        """Returns the SQL representation of this field for use in expressions."""
        if self.parent_model is None:
            raise ValueError(f"Field '{self.name}' is not associated with any model.")
        return f"{self.parent_model.__tablename__}.{self.name}"

    def __right_expression_input(self, value: Any) -> str:
        """Returns the SQL representation of a value for use in expressions."""
        if isinstance(value, Field):
            if value.parent_model is None:
                raise ValueError(f"Field '{value.name}' is not associated with any model.")
            return f"{value.parent_model.__tablename__}.{value.name}"
        return value  # Use parameterized queries for values

    def As(self, alias: str) -> 'Any':
        from .selector import Alias
        return Alias(self, alias)
    
    def __eq__(self, other: Any) -> Expression:
        """Builds an equality Expression for this field."""
        return Expression(self.__left_expression_input(), '=', self.__right_expression_input(other))

    def __ne__(self, other: Any) -> Expression:
        """Builds an inequality Expression for this field."""
        return Expression(self.__left_expression_input(), '!=', self.__right_expression_input(other))

    def __lt__(self, other: Any) -> Expression:
        """Builds a less-than Expression for this field."""
        return Expression(self.__left_expression_input(), '<', self.__right_expression_input(other))

    def __le__(self, other: Any) -> Expression:
        """Builds a less-than-or-equal Expression for this field."""
        return Expression(self.__left_expression_input(), '<=', self.__right_expression_input(other))

    def __gt__(self, other: Any) -> Expression:
        """Builds a greater-than Expression for this field."""
        return Expression(self.__left_expression_input(), '>', self.__right_expression_input(other))

    def __ge__(self, other: Any) -> Expression:
        """Builds a greater-than-or-equal Expression for this field."""
        return Expression(self.__left_expression_input(), '>=', self.__right_expression_input(other))

    def like(self, pattern: str) -> Expression:
        """Builds a LIKE Expression for this field."""
        return Expression(self.__left_expression_input(), 'LIKE', pattern)

    def in_(self, items: Iterable[Any]) -> Expression:
        """Builds an IN Expression for this field."""
        return Expression(self.__left_expression_input(), 'IN', list(items))

    def not_in(self, items: Iterable[Any]) -> Expression:
        """Builds a NOT IN Expression for this field."""
        return Expression(self.__left_expression_input(), 'NOT IN', list(items))



class Integer(Field):
    def __init__(self, **kwargs):
        super().__init__(type='INTEGER', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, int):
            raise ValueError(f"Expected an integer for field '{self.name}', got {type(value).__name__}")
        return value


class BigInteger(Integer):
    def __init__(self, **kwargs):
        super().__init__(type='BIGINT', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, int):
            raise ValueError(f"Expected an integer for field '{self.name}', got {type(value).__name__}")
        return value


class Decimal(Field):
    def __init__(self, *, precision: int = 10, scale: int = 2, **kwargs):
        super().__init__(type='DECIMAL', **kwargs)
        self.precision = precision
        self.scale = scale

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError(f"Expected a number for field '{self.name}', got {type(value).__name__}")

        # Validação de precisão e escala
        str_value = f"{value:.{self.scale}f}"  # Formata o valor com a escala definida
        integer_part, _, fractional_part = str_value.partition('.')

        if len(integer_part) > (self.precision - self.scale):
            raise ValueError(f"Value '{value}' exceeds the maximum precision for field '{self.name}'")

        if len(fractional_part) > self.scale:
            raise ValueError(f"Value '{value}' exceeds the maximum scale for field '{self.name}'")
        
        return value

class String(Field):
    def __init__(self,*, max_length: int = 255, **kwargs):
        super().__init__(type='VARCHAR', **kwargs)
        self.max_length = max_length

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Expected a string for field '{self.name}', got {type(value).__name__}")
        if len(value) > self.max_length:
            raise ValueError(f"String length for field '{self.name}' exceeds maximum of {self.max_length}")
        return value
    
    def __str__(self):
        return super().__str__().removesuffix('>') + f" max_length={self.max_length}>"



class IntegerID(Integer):
    def __init__(self, primary_key: bool = True, unique: bool = True, **kwargs):
        super().__init__(primary_key=primary_key, unique=unique, **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        
        if value is not None and value <= 0:
            raise ValueError(f"ID field '{self.name}' must be a positive integer")
        return value



class UUID(String):
    def __init__(self, primary_key: bool = True, unique: bool = True, **kwargs):
        super().__init__(max_length= 36, primary_key=primary_key, unique=unique, **kwargs)


    def validate_uuid_format(self, value: str) -> bool:
        from uuid import UUID
        try:
            UUID(value)
            return True
        except ValueError:
            return False


    def __validate__(self, value):
        from uuid import uuid4

        if value is None:
            value = str(uuid4())  # Gera um UUID aleatório se nenhum valor for fornecido
        else:
            if not self.validate_uuid_format(value):
                raise ValueError(f"Invalid UUID format for field '{self.name}': {value}")

        value = super().__validate__(value)
        return value



class Boolean(Field):
    def __init__(self,*args, **kwargs):
        super().__init__(type='BOOLEAN', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, bool):
            try:
                value = bool(value)
            except:
                raise ValueError(f"Expected a boolean for field '{self.name}', got {type(value).__name__}")
        return value


class Float(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='FLOAT', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError(f"Expected a number for field '{self.name}', got {type(value).__name__}")
        return value

class Text(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='TEXT', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Expected a string for field '{self.name}', got {type(value).__name__}")
        return value


class Blob(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='BLOB', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)
        if value is not None and not isinstance(value, (bytes, bytearray)):
            raise ValueError(f"Expected bytes for field '{self.name}', got {type(value).__name__}")
        return value


class DateTime(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='DATETIME', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)

        from datetime import datetime

        if value is not None and not isinstance(value, (datetime, str)):
            raise ValueError(f"Expected a datetime object or string for field '{self.name}', got {type(value).__name__}")
        
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"String value for field '{self.name}' must be in ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        return value


class Date(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='DATE', **kwargs)

    def __validate__(self, value):
        value = super().__validate__(value)

        from datetime import date
        if value is not None and not isinstance(value, (date, str)):
            raise ValueError(f"Expected a date object or string for field '{self.name}', got {type(value).__name__}")

        if isinstance(value, str):
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError(f"String value for field '{self.name}' must be in ISO format (YYYY-MM-DD)")
        
        return value

class Time(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='TIME', **kwargs)
    
    def __validate__(self, value):
        value = super().__validate__(value)

        from datetime import time
        if value is not None and not isinstance(value, (time, str)):
            raise ValueError(f"Expected a time object or string for field '{self.name}', got {type(value).__name__}")
        
        if isinstance(value, str):
            try:
                value = time.fromisoformat(value)
            except ValueError:
                raise ValueError(f"String value for field '{self.name}' must be in ISO format (HH:MM:SS)")
            
        return value