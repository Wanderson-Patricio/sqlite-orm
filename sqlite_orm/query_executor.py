from .query_builder import QueryBuilder
from .errors import InvalidMethodAssociationException

class QueryDebugger:
    """Utility class for logging SQL queries with parameters for debugging purposes."""
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
    """Maps raw database rows to model instances based on the model's field definitions."""
    def __init__(self, model):
        self.model = model
        self.fields = list(model._fields.keys())

    def _validate(self, row):
        if len(self.fields) != len(row):
            raise ValueError(
                "The number of fields in the model does not match the number of columns returned by the query."
            )

    def map_row(self, row):
        self._validate(row)
        return self.model(**dict(zip(self.fields, row)))

    def map_many(self, rows):
        return [self.map_row(row) for row in rows]


class SelectResultHandler:
    """Handles the results of a SELECT query, mapping them to model instances if required."""
    def __init__(self, cursor, options, model=None):
        self.cursor = cursor
        self.options = options
        self.mapper = ResultMapper(model) if options.to_model else None

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
        return rows

    def _handle_first(self):
        row = self.cursor.fetchone()
        if row and self.mapper:
            return self.mapper.map_row(row)
        return row
    

class QueryExecutor:
    """Executes SQL queries using the provided connection and query builder."""
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
            raise ValueError(
                f"Erro ao executar a consulta: {query} "
                f"com parâmetros: {parameters}. Detalhes: {e}"
            )
