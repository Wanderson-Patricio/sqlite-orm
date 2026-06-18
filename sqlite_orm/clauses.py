from typing import List, Optional
from dataclasses import dataclass, field

from .query_filter import QueryFilter


@dataclass
class QueryClauses:
    """
    Represents the clauses of a SQL query.

    Attributes:
        filters (List[QueryFilter]): A list of filter-like nodes to apply in the
            WHERE clause. Each node must implement generate_clause() and
            get_values() (for example, QueryFilter or Expression).
        order_by (Optional[str]): The column(s) to order the results by.
        limit (Optional[int]): The maximum number of rows to return.
        offset (Optional[int]): The number of rows to skip before starting to return rows.
    """
    filters: List[QueryFilter] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class FilterClauseGenerator:
    """
    Generates the WHERE clause from a list of filter-like objects.

    Methods:
        generate(filters: List[QueryFilter]) -> str:
            Generates the WHERE clause as a string.

    Raises:
        AttributeError: If a filter node does not implement generate_clause().
    """
    @staticmethod
    def generate(filters: List[QueryFilter]) -> str:
        clauses = []
        # Filtros passados de forma sequencial na raiz (ex: .filter(A, B)) atuarão como um AND global
        for filter_node in filters:
            clauses.append(f"({filter_node.generate_clause()})")
        return " AND ".join(clauses)
    

class ClauseGenerator:
    """
    Generates the full SQL clause (WHERE, ORDER BY, LIMIT, OFFSET) from a QueryClauses object.

    Methods:
        generate(clauses: QueryClauses) -> str:
            Generates the full SQL clause as a string.

    Notes:
        This generator is agnostic to the concrete filter class and relies on
        the filter node protocol consumed by FilterClauseGenerator.
    """
    @staticmethod
    def generate(clauses: QueryClauses) -> str:
        parts = []
        if clauses.filters:
            parts.append("WHERE " + FilterClauseGenerator.generate(clauses.filters))
        if clauses.order_by:
            parts.append(f"ORDER BY {clauses.order_by}")
        if clauses.limit is not None:
            parts.append(f"LIMIT {clauses.limit}")
        if clauses.offset is not None:
            parts.append(f"OFFSET {clauses.offset}")
        return " ".join(parts)