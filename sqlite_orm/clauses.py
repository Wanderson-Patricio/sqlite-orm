from typing import List, Optional
from dataclasses import dataclass, field

from .query_filter import QueryFilter


@dataclass
class QueryClauses:
    filters: List[QueryFilter] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class FilterClauseGenerator:
    @staticmethod
    def generate(filters: List[QueryFilter]) -> str:
        clauses = []
        # Filtros passados de forma sequencial na raiz (ex: .filter(A, B)) atuarão como um AND global
        for filter_node in filters:
            clauses.append(f"({filter_node.generate_clause()})")
        return " AND ".join(clauses)
    

class ClauseGenerator:
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