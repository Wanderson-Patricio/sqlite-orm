from sqlite3 import (IntegrityError,
    OperationalError,
    ProgrammingError,
    DatabaseError,
    DataError, 
    InterfaceError, 
    Error
)


class ValidationError(Exception):
    pass

class NotFilteredQueryException(Exception):
    pass

class InvalidMethodAssociationException(Exception):
    pass

class MethodPrecedenceException(Exception):
    pass


class ExceptionHandler:
    @staticmethod
    def handle_execution_error(query, parameters, exception):
        match type(exception).__name__:
            case IntegrityError.__name__:
                error_message = "Failed to execute query due to integrity constraints violation."
            case OperationalError.__name__:
                error_message = "Failed to execute query due to operational issues with the database."
            case ProgrammingError.__name__:
                error_message = "Failed to execute query due to a programming error."
            case DatabaseError.__name__:
                error_message = "Failed to execute query due to a database error."
            case DataError.__name__:
                error_message = "Failed to execute query due to a data error."
            case InterfaceError.__name__:
                error_message = "Failed to execute query due to an interface error."
            case Error.__name__:
                error_message = "Failed to execute query due to a general SQLite error."
            case _:
                error_message = "Failed to execute query due to an unknown error."

        raise ValueError(
            f"Error Executing Query: {query} "
            f"with parameters: {parameters}. Details: {error_message} - {exception}"
        )