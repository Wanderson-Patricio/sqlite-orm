from typing import Any, Optional, List, Callable
from dataclasses import InitVar, dataclass, field


from .model import Model
from .field import Field
from .query_filter import QueryFilter, AND
from .expression import Expression
from .errors import (
    InvalidMethodAssociationException,
    MethodPrecedenceException
)

from .query_builder import QueryBuilder, NOT_INSERTABLE_FIELDS
from .query_executor import QueryExecutor



@dataclass(frozen=True)
class ModelAttribute:
    """
    Represents a model attribute with its name and type.

    Attributes:
        name (str): The name of the attribute.
        type (str): The data type of the attribute.
    """
    name: str
    type: str


@dataclass
class OrderOption:
    """
    Represents the ordering options for a query.

    Attributes:
        field (Field): The field name to order by.
        ascending (bool): Whether to order in ascending
    """
    field: InitVar[Field]
    field_name: str = field(init=False)
    ascending: bool = True

    def __post_init__(self, field: Field):
        self.field_name = f"{field.parent_model.__tablename__}.{field.name}" if hasattr(field, 'parent_model') and field.parent_model is not None else str(field)


@dataclass
class JoinOption:
    """
    Represents a join option for a query.

    Attributes:
        join_model (Model): The model to join with.
        join_field (str): The field in the join model to use for the join condition.
        base_field (str): The field in the base model to use for the join condition.
        join_type (str): The type of join (e.g., INNER, LEFT, RIGHT).
    """
    models: List[Model] = field(default_factory=list)
    expression: Optional[Expression] = None
    types: List[str] = field(default_factory=list)

    @staticmethod
    def verify_join_type(join_type: str):
        """Verifies if the provided join type is valid."""
        valid_types = ["INNER", "LEFT", "RIGHT", "FULL"]
        if join_type not in valid_types:
            raise ValueError(f"Invalid join type '{join_type}'. Valid types are: {', '.join(valid_types)}.")


@dataclass
class SessionOptions:
    """
    Represents the configuration options for a database session.

    Attributes:
        model_attributes (List[str]): List of model attributes to include in queries.
        filters (List[Any]): List of filter nodes to apply to the query.
            Supported nodes are objects that implement generate_clause() and
            get_values(), such as Expression and QueryFilter.
        order_by (Optional[str]): Column to order the results by.
        limit (Optional[int]): Maximum number of rows to return.
        offset (Optional[int]): Number of rows to skip before returning results.
        method (Optional[str]): The SQL method (e.g., SELECT, INSERT, UPDATE, DELETE).
        parameters (List): Parameters to bind to the query.
        get_all (Optional[bool]): Whether to fetch all results or just the first.
        to_model (Optional[bool]): Whether to map results to model instances.
        update_set_clauses (List[str]): Fields to update in an UPDATE query.
        debug (Optional[bool]): Whether to enable debug mode.
        inserted_model (Optional[Model]): The model instance that was inserted, if applicable.

    Methods:
        reset():
            Resets all session options to their default values.
    """

    model_attributes: List[ModelAttribute] = field(default_factory=list)
    selected_fields: List[Any] = field(default_factory=list)
    filters: List[Any] = field(default_factory=list)
    order_by: Optional[OrderOption] = None
    group_by: Optional[List[str]] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    method: Optional[str] = None
    parameters: List = field(default_factory=list)
    get_all: Optional[bool] = None
    to_model: Optional[bool] = False
    update_set_clauses: List[str] = field(default_factory=list)
    debug: Optional[bool] = None
    inserted_model: Optional[Model] = None
    join_options: Optional[JoinOption] = None

    def reset(self):
        self.filters = []
        self.order_by = None
        self.group_by = []
        self.limit = None
        self.offset = None
        self.method = None
        self.parameters = []
        self.get_all = None
        self.to_model = False
        self.update_set_clauses = []
        self.selected_fields = []
        self.inserted_model = None
        self.join_options = []


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
            Adds filters to the query using Expression objects, QueryFilter
            objects, or keyword equality filters.
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
    def __init__(self, model: Model, db):
        self.model = model
        self.conn = db.connection
        self.options = SessionOptions(
            model_attributes=list(
                map(lambda attr: ModelAttribute(name=attr, type=str(type(model._fields[attr]).__name__)), model._fields.keys())
            ),
            filters=[],
            parameters=[],
            update_set_clauses=[],
            debug=False
        )


    @property
    def attributes(self) -> List[str]:
        """Returns a list of attribute names for the model associated with the session."""
        return [
            attr.name for attr in self.options.model_attributes
            if attr.type not in NOT_INSERTABLE_FIELDS
        ]
    

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
    

    def select(self, *fields: Any):
        """Sets the session's method to SELECT for building a SELECT query."""
        self.options.method = "SELECT"
        if fields:
            self.options.selected_fields = list(fields)
        return self
    

    def insert(self, model_instance: Model):
        """Sets the session's method to INSERT for building an INSERT query and prepares the parameters."""
        self.options.method = "INSERT"
        self.options.inserted_model = model_instance

        self.options.parameters = [
            getattr(model_instance, attr)
            for attr in self.attributes
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
    def set(self, *args: Expression):
        """Sets the fields and values for an UPDATE query. Must be called before .where() for UPDATE queries."""
        if not args:
            return self  # No arguments provided, do nothing

        if not all(isinstance(arg, Expression) for arg in args):
            raise TypeError("All arguments to .set() must be Expression instances.")
        
        for arg in args:
            key = arg.left
            value = arg.right
            self.options.parameters.append(value)
            # Strip table qualifier (e.g. "users.name" → "name"); SQLite rejects table.column in SET
            column = key.split(".")[-1] if isinstance(key, str) and "." in key else key
            self.options.update_set_clauses.append(column)
            
        return self
    

    def where(self, *filters: Any, **kwargs):
        """Adds filter nodes to the query.

        Accepted styles:
                - Expression objects (recommended):
                    .where(User.id == 1)
                - Composed expressions:
                    .where((User.age > 18) & (User.name.like("A%")))
                - Legacy QueryFilter kwargs:
                    .where(id=Equals(1))
                - Keyword equality shortcut:
                    .where(id=1)

        Notes:
                - Multiple root filters passed in the same call are combined with
                    a global AND by the clause generator.
                - For UPDATE queries, .set() must be called before .where().
        """
        if self.options.method == "UPDATE" and (not self.options.parameters):
            raise MethodPrecedenceException("When on update method, the setters must be passed before the filters.")

        normalized_filters: List[Any] = list(filters)

        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, QueryFilter):
                    normalized_filters.append(AND(**{key: value}))
                else:
                    normalized_filters.append(Expression(key, '=', value))

        for filter_node in normalized_filters:
            if not hasattr(filter_node, "generate_clause") or not hasattr(filter_node, "get_values"):
                raise TypeError(
                    "Filters must be Expression or QueryFilter instances. "
                    "Examples: .where(User.id == 1) or .where(id=Equals(1))."
                )
            self.options.filters.append(filter_node)
            self.options.parameters.extend(filter_node.get_values())

        return self


    @Helpers.only("SELECT")
    def order_by(self, field: Any, ascending: bool = True):
        """Sets the ORDER BY clause for a SELECT query."""
        # field_name = field.name if hasattr(field, 'name') else str(field)
        # if field_name not in self.model._fields:
        #     raise AttributeError(f"Attribute '{field_name}' is not valid for model '{self.model.__name__}'")
        self.options.order_by = OrderOption(field=field, ascending=ascending)
        return self


    @Helpers.only("SELECT")
    def group_by(self, *fields: Field):
        """Sets the GROUP BY clause for a SELECT query."""
        group_by_fields = []
        for field in fields:
            if hasattr(field, 'parent_model') and field.parent_model is not None:
                group_by_fields.append(f"{field.parent_model.__tablename__}.{field.name}")
            else:
                group_by_fields.append(field.name if hasattr(field, 'name') else str(field))
        self.options.group_by = group_by_fields
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
    def join(self, related_model: Model, type: str = "INNER"):
        if not self.options.selected_fields:
            raise ValueError("You must call .select() with specified fields before specifying a JOIN.")
        if not self.options.join_options:
            self.options.join_options = JoinOption()
        self.options.join_options.models.append(related_model)

        JoinOption.verify_join_type(type.upper())
        self.options.join_options.types.append(type.upper())
        return self
    

    @Helpers.only("SELECT")
    def on(self, expression: Expression):
        if not self.options.join_options:
            raise ValueError("You must call .join() before specifying the ON condition.")
        self.options.join_options.expression = expression
        return self



    @Helpers.only("SELECT")
    def to_model(self):
        """Indicates that the results of a SELECT query should be mapped to model instances."""
        from .selector import Alias

        for field in self.options.selected_fields:
            if not isinstance(field, Alias):
                raise ValueError(f"Field '{field}' is not associated with a alias.")

            # if not hasattr(field.element, 'parent_model') or field.element.parent_model != self.model:
            #     raise ValueError(f"Field '{field}' is not associated with the model '{self.model.__name__}'.")
            
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
