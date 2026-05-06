import sqlite3
    

def get_database_connection(db_name: str):
    """
    Establish a connection to the SQLite database using the provided database name.

    Args:
        db_name (str): The name of the SQLite database file.

    Returns:
        sqlite3.Connection: A SQLite database connection object.

    Raises:
        sqlite3.Error: If there is an error connecting to the database.
    """
    try:
        return sqlite3.connect(db_name)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise e

class DatabaseContextManager:
    """
    A context manager for managing database connections.

    Attributes:
        db_name (str): The name of the SQLite database file.
        connection (sqlite3.Connection): The SQLite database connection object.

    Methods:
        table_exists(table_name: str) -> bool:
            Checks if a table exists in the database.
    """
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None


    def __enter__(self):
        self.connection = get_database_connection(self.db_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name (str): The name of the table to check.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        return cursor.fetchone() is not None