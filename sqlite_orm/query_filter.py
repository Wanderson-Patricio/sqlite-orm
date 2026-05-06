from typing import Any, List


class QueryFilter:
    """
    Base class for all query filters.

    Responsibilities:
        - Define the interface for generating SQL query clauses.
        - Provide methods to retrieve filter values.

    Attributes:
        query_symbol (str): The SQL operator or symbol for the filter (e.g., '=', '!=', 'LIKE').
        value (Any): The value associated with the filter.

    Methods:
        generate_clause() -> str:
            Generates the SQL clause for the filter.
        get_values() -> List[Any]:
            Retrieves the values associated with the filter.

    Raises:
        NotImplementedError: If the generate_clause or get_values methods are not implemented in a subclass.
    """
    def __init__(self, query_symbol: str, value: Any):
        self.query_symbol = query_symbol
        self.value = value



class AND(QueryFilter):
    """Represents an AND logical operator in a query filter."""
    def __init__(self, *nested_filters: 'QueryFilter', **field_filters: QueryFilter):
        super().__init__('AND', None)
        self.nested_filters = nested_filters
        self.field_filters = field_filters

    def generate_clause(self) -> str:
        clauses = []
        # Adiciona as cláusulas aninhadas (outros ANDs e ORs)
        for filter_node in self.nested_filters:
            clauses.append(f"({filter_node.generate_clause()})")
        
        # Adiciona as cláusulas de campo (ex: cpf=Equal(...))
        for key, value in self.field_filters.items():
            clauses.append(f"{key} {value.query_symbol} ?")
            
        return " AND ".join(clauses)

    def get_values(self) -> List[Any]:
        values = []
        for filter_node in self.nested_filters:
            values.extend(filter_node.get_values())
        for value in self.field_filters.values():
            values.append(value.value)
        return values


class OR(QueryFilter):
    """Represents an OR logical operator in a query filter."""
    def __init__(self, *nested_filters: 'QueryFilter', **field_filters: QueryFilter):
        super().__init__('OR', None)
        self.nested_filters = nested_filters
        self.field_filters = field_filters

    def generate_clause(self) -> str:
        clauses = []
        for filter_node in self.nested_filters:
            clauses.append(f"({filter_node.generate_clause()})")
            
        for key, value in self.field_filters.items():
            clauses.append(f"{key} {value.query_symbol} ?")
            
        return " OR ".join(clauses)

    def get_values(self) -> List[Any]:
        values = []
        for filter_node in self.nested_filters:
            values.extend(filter_node.get_values())
        for value in self.field_filters.values():
            values.append(value.value)
        return values


class Equals(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('=', value)


class NotEquals(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('!=', value)


class GreaterThan(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('>', value)


class GreaterThanOrEqual(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('>=', value)


class LessThan(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('<', value)


class LessThanOrEqual(QueryFilter):
    def __init__(self, value: Any):
        super().__init__('<=', value)


class Like(QueryFilter):
    def __init__(self, value: str):
        super().__init__('LIKE', value)


class In(QueryFilter):
    def __init__(self, value: List[Any]):
        super().__init__('IN', value)