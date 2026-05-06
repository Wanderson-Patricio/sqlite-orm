from abc import ABC, abstractmethod

from .errors import (
    NotFilteredQueryException,
    InvalidMethodAssociationException
)

from .clauses import ClauseGenerator

class BuilderFactory(ABC):
    """
    Abstract base class for all query builders.

    Responsibilities:
        - Define the interface for building SQL queries.
        - Serve as a base class for specific query builders.

    Attributes:
        session: The database session containing query options.

    Methods:
        build():
            Abstract method to build the SQL query string.

    Raises:
        NotImplementedError: If the build method is not implemented in a subclass.
    """
    def __init__(self, session):
        self.session = session

    @abstractmethod
    def build(self):
        pass


class SelectQueryBuilder(BuilderFactory):
    """
    Builds SELECT SQL queries based on session options.

    Methods:
        build() -> str:
            Constructs the SELECT query string.

    Raises:
        InvalidMethodAssociationException: If required options are not set for the query.

    Returns:
        str: The constructed SELECT query string.
    """
    def build(self):
        options = self.session.options
        if not options.model_attributes:
            raise InvalidMethodAssociationException("Model must have at least one attribute to build a SELECT query.")
        if options.get_all is None:
            raise InvalidMethodAssociationException("Must specify .all() or .first() before executing a SELECT query.")
        if not options.get_all:
            options.limit = 1
        return f"SELECT {', '.join(options.model_attributes)} FROM {self.session.model.__tablename__} {ClauseGenerator.generate(options)};"


class InsertQueryBuilder(BuilderFactory):
    """
    Builds INSERT SQL queries based on session options.

    Methods:
        build() -> str:
            Constructs the INSERT query string.

    Returns:
        str: The constructed INSERT query string.
    """
    def build(self) -> str:
        attributes = [
            attr for attr in self.session.options.model_attributes
            if attr != "id"
        ]

        placeholders = ", ".join(["?"] * len(attributes))

        return (
            f"INSERT INTO {self.session.model.__tablename__} "
            f"({', '.join(attributes)}) "
            f"VALUES ({placeholders});"
        )
    

class UpdateQueryBuilder(BuilderFactory):
    """
    Builds UPDATE SQL queries based on session options.

    Methods:
        build() -> str:
            Constructs the UPDATE query string.

    Raises:
        NotFilteredQueryException: If no filters are provided for the query.

    Returns:
        str: The constructed UPDATE query string.
    """
    def build(self) -> str:
        options = self.session.options

        if not options.filters:
            raise NotFilteredQueryException(
                "UPDATE queries must have at least one filter."
            )

        set_clause = ", ".join(
            f"{attr}=?" for attr in options.update_set_clauses
        )

        return (
            f"UPDATE {self.session.model.__tablename__} "
            f"SET {set_clause} "
            f"{ClauseGenerator.generate(options)};"
        )
    

class DeleteQueryBuilder(BuilderFactory):
    """
    Builds DELETE SQL queries based on session options.

    Methods:
        build() -> str:
            Constructs the DELETE query string.

    Raises:
        NotFilteredQueryException: If no filters are provided for the query.

    Returns:
        str: The constructed DELETE query string.
    """
    def build(self) -> str:
        options = self.session.options

        if not options.filters:
            raise NotFilteredQueryException(
                "DELETE queries must have at least one filter."
            )

        return (
            f"DELETE FROM {self.session.model.__tablename__} "
            f"{ClauseGenerator.generate(options)};"
        )


class CreateTableQueryBuilder(BuilderFactory):
    """
    Builds CREATE TABLE SQL queries based on the model's field definitions.

    Methods:
        build() -> str:
            Constructs the CREATE TABLE query string.

    Returns:
        str: The constructed CREATE TABLE query string.
    """
    def build(self) -> str:
        field_definitions = []

        for field_name, field in self.session.model._fields.items():
            definition = f"{field_name} {field.type.upper()}"

            if field.type.upper() == "VARCHAR" and hasattr(field, "max_length"):
                definition += f"({field.max_length})"

            if field.primary_key:
                definition += " PRIMARY KEY"
            if not field.nullable:
                definition += " NOT NULL"
            if field.unique:
                definition += " UNIQUE"

            field_definitions.append(definition)

        return (
            f"CREATE TABLE IF NOT EXISTS "
            f"{self.session.model.__tablename__} "
            f"({', '.join(field_definitions)});"
        )
    

class DropTableQueryBuilder(BuilderFactory):
    """
    Builds DROP TABLE SQL queries.

    Methods:
        build() -> str:
            Constructs the DROP TABLE query string.

    Returns:
        str: The constructed DROP TABLE query string.
    """
    def build(self) -> str:
        return f"DROP TABLE IF EXISTS {self.session.model.__tablename__};"


class QueryBuilder(BuilderFactory):
    """
    Factory class that selects the appropriate query builder based on the session's options.

    Responsibilities:
        - Delegate the query building process to the appropriate builder class.

    Methods:
        build() -> str:
            Constructs the SQL query string using the appropriate builder.

    Raises:
        ValueError: If the query method is unsupported.

    Returns:
        str: The constructed SQL query string.
    """
    def build(self) -> str:
        builder_map = {
            "SELECT": SelectQueryBuilder,
            "INSERT": InsertQueryBuilder,
            "UPDATE": UpdateQueryBuilder,
            "DELETE": DeleteQueryBuilder,
            "CREATE_TABLE": CreateTableQueryBuilder,
            "DROP_TABLE": DropTableQueryBuilder,
        }

        builder_cls = builder_map.get(self.session.options.method)

        if not builder_cls:
            raise ValueError(
                f"Unsupported query method: {self.session.options.method}"
            )

        return builder_cls(self.session).build()