from typing import Optional, List, Callable
from dataclasses import dataclass, field


from .model import Model
from .query_filter import QueryFilter, AND
from .database_manager import DatabaseContextManager
from .errors import (
    InvalidMethodAssociationException,
    MethodPrecedenceException
)

from .query_builder import QueryBuilder
from .query_executor import QueryExecutor


@dataclass
class SessionOptions:
    model_attributes: List[str]
    # Agora filters é uma lista simples, pois as árvores ficam dentro dos próprios filtros
    filters: List[QueryFilter] = field(default_factory=list) 
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    method: Optional[str] = None
    parameters: List = field(default_factory=list)
    get_all: Optional[bool] = None
    to_model: Optional[bool] = False
    update_set_clauses: List[str] = field(default_factory=list)
    debug: Optional[bool] = None

    def reset(self):
        self.filters = []
        self.order_by = None
        self.limit = None
        self.offset = None
        self.method = None
        self.parameters = []
        self.get_all = None
        self.to_model = False
        self.update_set_clauses = []




class Helpers:
    @staticmethod
    def only(method: str = 'SELECT'):
        def only_implementation(func: Callable):
            def wrapper(self, *args, **kwargs):
                if self.options.method != method:
                    raise InvalidMethodAssociationException(f"The method '{func.__name__}' can only be used with {method} queries.")
                return func(self, *args, **kwargs)
            return wrapper
        return only_implementation


class DBSession:
    def __init__(self, model: Model, db: DatabaseContextManager):
        self.model = model
        self.conn = db.connection
        self.options = SessionOptions(
            model_attributes=list(self.model._fields),
            filters=[],
            parameters=[],
            update_set_clauses=[],
            debug=False
        )

    def debug(self, enable: bool = True, in_place: bool = False):
        self.options.debug = enable
        if not in_place:
            return self

    def reset_options(self):
        self.options.reset()

    def create_table(self):
        self.options.method = "CREATE_TABLE"
        return self
    
    def drop_table(self):
        self.options.method = "DROP_TABLE"
        return self

    def select(self):
        self.options.method = "SELECT"
        return self

    def insert(self, model_instance: Model):
        self.options.method = "INSERT"
        self.options.parameters = [
            getattr(model_instance, attr)
            for attr in self.options.model_attributes
            if attr != "id"
        ]
        return self

    def delete(self):
        self.options.method = "DELETE"
        return self

    def update(self):
        self.options.method = "UPDATE"
        return self
    
    @Helpers.only("UPDATE")
    def set(self, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                if key not in self.options.model_attributes:
                    raise AttributeError(f"Attribute '{key}' is not valid for model '{self.model.__name__}'")
                self.options.parameters.append(value)
                self.options.update_set_clauses.append(key)
        return self

    def where(self, *filters: QueryFilter, **kwargs): # Alterado de AND | OR para aceitar qualquer QueryFilter
        if self.options.method == "UPDATE" and (not self.options.parameters):
            raise MethodPrecedenceException("When on update method, the setters must be passed before the filters.")

        if kwargs:
            filters = list(filters) # Converte os filtros posicionais para uma lista mutável
            filters.append(AND(**{key: value for key, value in kwargs.items()})) # Transforma os filtros de campo passados via kwargs em um AND e o adiciona à lista de filtros. Assim, .filter(cpf=Equal(...), name=Equal(...)) se torna .filter(AND(cpf=Equal(...), name=Equal(...)))

        # Apenas adiciona os filtros diretos à lista base
        for filter_node in filters:
            self.options.filters.append(filter_node)
            self.options.parameters.extend(filter_node.get_values())

        return self

    @Helpers.only("SELECT")
    def order_by(self, field_name: str):
        if field_name not in self.model._fields:
            raise AttributeError(f"Attribute '{field_name}' is not valid for model '{self.model.__name__}'")
        self.options.order_by = field_name
        return self

    @Helpers.only("SELECT")
    def limit(self, limit: int):
        if not isinstance(limit, int):
            raise ValueError("Limit must be an integer.")
        self.options.limit = limit
        return self

    @Helpers.only("SELECT")
    def offset(self, offset: int):
        if not isinstance(offset, int):
            raise ValueError("Offset must be an integer.")
        self.options.offset = offset
        return self
    
    @Helpers.only("SELECT")
    def all(self):
        self.options.get_all = True
        return self

    @Helpers.only("SELECT")
    def first(self):
        self.options.get_all = False
        self.options.limit = 1
        return self

    @Helpers.only("SELECT")
    def to_model(self):
        self.options.to_model = True
        return self

    def execute(self):
        query_builder = QueryBuilder(self)
        executor = QueryExecutor(self.conn, query_builder)
        result = executor.execute()
        self.reset_options() # Reseta as opções após a execução para evitar vazamento de estado entre consultas
        return result
