from abc import ABC, abstractmethod

class Field(ABC):
    """
    Base class for all field types in the ORM.
    """

    def __init__(self,
                 *,
                 type: str, 
                 primary_key: bool = False, 
                 nullable: bool = True, 
                 unique: bool = False
                ) -> None:
        
        self.name = None
        self.__type = type
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique

    def __str__(self):
        return f"<Field name={self.name} type={self.__type} primary_key={self.primary_key} nullable={self.nullable} unique={self.unique}>"

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
        if not self.nullable and value is None:
            raise ValueError(f"Field '{self.name}' cannot be null")


class Integer(Field):
    def __init__(self, **kwargs):
        super().__init__(type='INTEGER', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, int):
            raise ValueError(f"Expected an integer for field '{self.name}', got {type(value).__name__}")
        return value


class ID(Integer):
    def __init__(self):
        super().__init__(primary_key=True, unique=True)

    def __validate__(self, value):
        value = super().__validate__(value)
        
        if value <= 0:
            raise ValueError(f"ID field '{self.name}' must be a positive integer")
        return value


class BigInteger(Integer):
    def __init__(self, **kwargs):
        super().__init__(type='BIGINT', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, int):
            raise ValueError(f"Expected an integer for field '{self.name}', got {type(value).__name__}")
        return value


class Decimal(Field):
    def __init__(self, *, precision: int = 10, scale: int = 2, **kwargs):
        super().__init__(type='DECIMAL', **kwargs)
        self.precision = precision
        self.scale = scale

    def __validate__(self, value):
        if not isinstance(value, (int, float)):
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
        if not isinstance(value, str):
            raise ValueError(f"Expected a string for field '{self.name}', got {type(value).__name__}")
        if len(value) > self.max_length:
            raise ValueError(f"String length for field '{self.name}' exceeds maximum of {self.max_length}")
        return value
    
    def __str__(self):
        return super().__str__().removesuffix('>') + f" max_length={self.max_length}>"


class Boolean(Field):
    def __init__(self,*args, **kwargs):
        super().__init__(type='BOOLEAN', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, bool):
            raise ValueError(f"Expected a boolean for field '{self.name}', got {type(value).__name__}")


class Float(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='FLOAT', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected a number for field '{self.name}', got {type(value).__name__}")

class Text(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='TEXT', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, str):
            raise ValueError(f"Expected a string for field '{self.name}', got {type(value).__name__}")


class Blob(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='BLOB', **kwargs)

    def __validate__(self, value):
        if not isinstance(value, (bytes, bytearray)):
            raise ValueError(f"Expected bytes for field '{self.name}', got {type(value).__name__}")


class DateTime(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(type='DATETIME', **kwargs)

    def __validate__(self, value):
        from datetime import datetime

        if not isinstance(value, (datetime, str)):
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
        from datetime import date
        if not isinstance(value, (date, str)):
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
        from datetime import time
        if not isinstance(value, (time, str)):
            raise ValueError(f"Expected a time object or string for field '{self.name}', got {type(value).__name__}")
        
        if isinstance(value, str):
            try:
                value = time.fromisoformat(value)
            except ValueError:
                raise ValueError(f"String value for field '{self.name}' must be in ISO format (HH:MM:SS)")
            
        return value