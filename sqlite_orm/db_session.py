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
    """
    Represents the configuration options for a database session.

    Attributes:
        model_attributes (List[str]): List of model attributes to include in queries.
        filters (List[QueryFilter]): List of filters to apply to the query.
        order_by (Optional[str]): Column to order the results by.
        limit (Optional[int]): Maximum number of rows to return.
        offset (Optional[int]): Number of rows to skip before returning results.
        method (Optional[str]): The SQL method (e.g., SELECT, INSERT, UPDATE, DELETE).
        parameters (List): Parameters to bind to the query.
        get_all (Optional[bool]): Whether to fetch all results or just the first.
        to_model (Optional[bool]): Whether to map results to model instances.
        update_set_clauses (List[str]): Fields to update in an UPDATE query.
        debug (Optional[bool]): Whether to enable debug mode.

    Methods:
        reset():
            Resets all session options to their default values.
    """

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
    """
    Utility class for helper decorators and functions used in DBSession.

    Methods:
        only(method: str):
            Decorator to restrict a method to a specific SQL operation.

    Raises:
        InvalidMethodAssociationException: If the method is used with an invalid SQL operation.
    """

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
    """
    Represents a database session for a specific model, allowing the construction and execution of SQL queries.

    Responsibilities:
        - Manage the state and options for SQL queries.
        - Provide a fluent interface for building and executing queries.

    Attributes:
        model (Model): The model associated with the session.
        conn (sqlite3.Connection): The database connection.
        options (SessionOptions): The configuration options for the session.

    Methods:
        debug(enable: bool, in_place: bool):
            Enables or disables debug mode for the session.
        reset_options():
            Resets the session's options to their default state.
        create_table():
            Sets the session's method to CREATE_TABLE.
        drop_table():
            Sets the session's method to DROP_TABLE.
        select():
            Sets the session's method to SELECT.
        insert(model_instance: Model):
            Sets the session's method to INSERT and prepares parameters.
        delete():
            Sets the session's method to DELETE.
        update():
            Sets the session's method to UPDATE.
        set(**kwargs):
            Sets fields and values for an UPDATE query.
        where(*filters, **kwargs):
            Adds filters to the query.
        order_by(field_name: str):
            Sets the ORDER BY clause for a SELECT query.
        limit(limit: int):
            Sets the LIMIT clause for a SELECT query.
        offset(offset: int):
            Sets the OFFSET clause for a SELECT query.
        all():
            Indicates that all results should be returned for a SELECT query.
        first():
            Indicates that only the first result should be returned for a SELECT query.
        to_model():
            Indicates that results should be mapped to model instances.
        execute():
            Builds, executes, and handles the SQL query.

    Raises:
        InvalidMethodAssociationException: If a method is used with an invalid SQL operation.
        MethodPrecedenceException: If .set() is not called before .where() for UPDATE queries.
        AttributeError: If an invalid attribute is used in a query.
        ValueError: If invalid values are provided for LIMIT or OFFSET.

    Returns:
        Any: The result of the executed query.
    """
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
        """Enables or disables debug mode for the session, which logs executed SQL queries with parameters."""
        self.options.debug = enable
        if not in_place:
            return self

    def reset_options(self):
        """Resets the session's options to their default state after query execution to prevent state leakage between queries."""
        self.options.reset()

    def create_table(self):
        """Sets the session's method to CREATE_TABLE for building a CREATE TABLE query."""
        self.options.method = "CREATE_TABLE"
        return self
    
    def drop_table(self):
        """Sets the session's method to DROP_TABLE for building a DROP TABLE query."""
        self.options.method = "DROP_TABLE"
        return self

    def select(self):
        """Sets the session's method to SELECT for building a SELECT query."""
        self.options.method = "SELECT"
        return self

    def insert(self, model_instance: Model):
        """Sets the session's method to INSERT for building an INSERT query and prepares the parameters."""
        self.options.method = "INSERT"
        self.options.parameters = [
            getattr(model_instance, attr)
            for attr in self.options.model_attributes
            if attr != "id"
        ]
        return self

    def delete(self):
        """Sets the session's method to DELETE for building a DELETE query."""
        self.options.method = "DELETE"
        return self

    def update(self):
        """Sets the session's method to UPDATE for building an UPDATE query."""
        self.options.method = "UPDATE"
        return self
    
    @Helpers.only("UPDATE")
    def set(self, **kwargs):
        """Sets the fields and values for an UPDATE query. Must be called before .where() for UPDATE queries."""
        if kwargs:
            for key, value in kwargs.items():
                if key not in self.options.model_attributes:
                    raise AttributeError(f"Attribute '{key}' is not valid for model '{self.model.__name__}'")
                self.options.parameters.append(value)
                self.options.update_set_clauses.append(key)
        return self

    def where(self, *filters: QueryFilter, **kwargs):
        """Adds filters to the query. For UPDATE queries, .set() must be called before .where()."""
        if self.options.method == "UPDATE" and (not self.options.parameters):
            raise MethodPrecedenceException("When on update method, the setters must be passed before the filters.")

        if kwargs:
            filters = list(filters)
            filters.append(AND(**{key: value for key, value in kwargs.items()}))

        for filter_node in filters:
            self.options.filters.append(filter_node)
            self.options.parameters.extend(filter_node.get_values())

        return self

    @Helpers.only("SELECT")
    def order_by(self, field_name: str):
        """Sets the ORDER BY clause for a SELECT query."""
        if field_name not in self.model._fields:
            raise AttributeError(f"Attribute '{field_name}' is not valid for model '{self.model.__name__}'")
        self.options.order_by = field_name
        return self

    @Helpers.only("SELECT")
    def limit(self, limit: int):
        """Sets the LIMIT clause for a SELECT query."""
        if not isinstance(limit, int):
            raise ValueError("Limit must be an integer.")
        self.options.limit = limit
        return self

    @Helpers.only("SELECT")
    def offset(self, offset: int):
        """Sets the OFFSET clause for a SELECT query."""
        if not isinstance(offset, int):
            raise ValueError("Offset must be an integer.")
        self.options.offset = offset
        return self
    
    @Helpers.only("SELECT")
    def all(self):
        """Indicates that all results should be returned for a SELECT query."""
        self.options.get_all = True
        return self

    @Helpers.only("SELECT")
    def first(self):
        """Indicates that only the first result should be returned for a SELECT query."""
        self.options.get_all = False
        self.options.limit = 1
        return self

    @Helpers.only("SELECT")
    def to_model(self):
        """Indicates that the results of a SELECT query should be mapped to model instances."""
        self.options.to_model = True
        return self

    def execute(self):
        """Builds the SQL query using the query builder, executes it,
        and handles the results based on the session's options."""
        query_builder = QueryBuilder(self)
        executor = QueryExecutor(self.conn, query_builder)
        result = executor.execute()
        self.reset_options() # Reseta as opções após a execução para evitar vazamento de estado entre consultas
        return result
