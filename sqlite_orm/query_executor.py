from .query_builder import QueryBuilder
from .errors import InvalidMethodAssociationException, ExceptionHandler

class QueryDebugger:
    """
    Utility class for logging SQL queries with parameters for debugging purposes.

    Responsibilities:
        - Format SQL queries with their parameters for debugging.
        - Log the formatted queries.

    Methods:
        format(query: str, parameters: list) -> str:
            Formats the SQL query with its parameters.
        log(query: str, parameters: list):
            Logs the formatted SQL query.
    """
    def __init__(self):
        import logging
        
        logging.basicConfig(
            level=logging.DEBUG,  # ou INFO em produção
            format="%(name)s - %(message)s",
        )

        self.logger = logging.getLogger(__name__)

    def format(self, query: str, parameters: list) -> str:
        debug_query = query
        for param in parameters:
            debug_query = debug_query.replace("?", repr(param), 1)
        return debug_query

    def log(self, query: str, parameters: list):
        self.logger.debug(
            "Executing query: %s",
            self.format(query, parameters)
        )


class ResultMapper:
    """
    Maps raw database rows to model instances based on the model's field definitions
    or creates dynamic model classes for custom SELECT projections.
    """
    def __init__(self, model, column_names, is_dynamic=False):
        self.model = model
        self.column_names = column_names
        self.is_dynamic = is_dynamic

        if self.is_dynamic:
            # Cria uma classe genérica em tempo de execução para comportar colunas customizadas
            self.target_class = type("DynamicRecord", (), {})
        else:
            self.target_class = model
            self.fields = list(model._fields.keys())

    def _validate(self, row):
        if not self.is_dynamic and len(self.fields) != len(row):
            raise ValueError(
                "The number of fields in the model does not match the number of columns returned by the query."
            )

    def map_row(self, row):
        self._validate(row)

        if self.is_dynamic:
            # Instancia a classe dinâmica e popula os atributos usando os nomes das colunas
            instance = self.target_class()
            for col_name, value in zip(self.column_names, row):
                setattr(instance, col_name, value)
            return instance
        else:
            # Mapeamento padrão para o modelo original
            return self.target_class(**dict(zip(self.fields, row)))

    def map_many(self, rows):
        return [self.map_row(row) for row in rows]


class SelectResultHandler:
    """
    Handles the results of a SELECT query, mapping them to model instances if required,
    or returning dictionaries for non-model queries.
    """
    def __init__(self, cursor, options, model=None):
        self.cursor = cursor
        self.options = options
        
        # Extrai os nomes das colunas/aliases do banco de dados
        self.column_names = [desc[0] for desc in cursor.description] if cursor.description else []

        if options.to_model:
            # Verifica se há seletores customizados nas opções (se o atributo existir e tiver itens)
            is_dynamic = bool(getattr(options, 'selected_fields', []))
            self.mapper = ResultMapper(model, self.column_names, is_dynamic)
        else:
            self.mapper = None

    def handle(self):
        if self.options.get_all is None:
            raise InvalidMethodAssociationException(
                "Must specify .all() or .first() before executing a SELECT query."
            )

        return self._handle_all() if self.options.get_all else self._handle_first()

    def _handle_all(self):
        rows = self.cursor.fetchall()
        
        if self.mapper:
            return self.mapper.map_many(rows)
            
        # Se to_model for False, retorna uma lista de dicionários
        return [dict(zip(self.column_names, row)) for row in rows]

    def _handle_first(self):
        row = self.cursor.fetchone()
        if not row:
            return None
            
        if self.mapper:
            return self.mapper.map_row(row)
            
        # Se to_model for False, retorna um dicionário único
        return dict(zip(self.column_names, row))
    

class QueryExecutor:
    """
    Executes SQL queries using the provided connection and query builder.

    Responsibilities:
        - Build SQL queries using the query builder.
        - Execute queries and handle results.
        - Commit changes for non-SELECT queries.

    Attributes:
        conn: The database connection.
        query_builder (QueryBuilder): The query builder for constructing SQL queries.
        options: The session options specifying query parameters and behavior.

    Methods:
        execute() -> Any:
            Builds, executes, and handles the SQL query.
        _execute_query(query: str, parameters: tuple):
            Executes the given SQL query with parameters.

    Raises:
        ValueError: If there is an error executing the query.

    Returns:
        Any: The result of the executed query, such as the number of affected rows or the query results.
    """
    def __init__(self, conn, query_builder: QueryBuilder):
        self.conn = conn
        self.query_builder = query_builder
        self.options = query_builder.session.options

    def execute(self):
        """Builds the SQL query using the query builder, executes it, 
        and handles the results based on the session's options."""
        query = self.query_builder.build()
        parameters = tuple(self.options.parameters)

        if self.options.debug:
            debugger = QueryDebugger()
            debugger.log(query, parameters)

        cursor = self._execute_query(query, parameters)

        if self.options.method == "SELECT":
            return SelectResultHandler(
                cursor,
                self.options,
                self.query_builder.session.model
            ).handle()

        self.conn.commit()

        if self.options.method == "INSERT":
            return cursor.lastrowid

        return cursor.rowcount

    def _execute_query(self, query, parameters):
        """Executes the given SQL query with parameters and returns the cursor."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            return cursor
        except Exception as e:
            ExceptionHandler.handle_execution_error(query, parameters, e)
