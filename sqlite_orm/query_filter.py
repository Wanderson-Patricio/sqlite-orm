from typing import Any, List
class QueryFilter:
    """Base class for all query filters."""
    def __init__(self, query_symbol: str, value: Any):
        self.query_symbol = query_symbol
        self.value = value

    def generate_clause(self) -> str:
        raise NotImplementedError("Subclasses must implement generate_clause.")

    def get_values(self) -> List[Any]:
        raise NotImplementedError("Subclasses must implement get_values.")


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