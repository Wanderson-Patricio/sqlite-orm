from typing import Any, Iterable, List


class Expression:
    """Represents a SQL predicate expression.

    An Expression can model simple comparisons (for example, id = 1),
    collection predicates (IN/NOT IN), NULL checks, or logical composition
    using AND, OR, and NOT. This object generates parameterized SQL fragments
    and the corresponding bind values for safe query execution.
    """
    def __init__(self, left: Any, operator: str, right: Any):
        self.left = left
        self.operator = operator
        self.right = right

    def __and__(self, other: 'Expression') -> 'Expression':
        """Combines two expressions using SQL AND."""
        return Expression(self, 'AND', other)
    
    def __or__(self, other: 'Expression') -> 'Expression':
        """Combines two expressions using SQL OR."""
        return Expression(self, 'OR', other)
    
    def __eq__(self, other: Any) -> 'Expression':
        """Builds an equality comparison expression."""
        return Expression(self, '=', other)
    
    def __ne__(self, other: Any) -> 'Expression':
        """Builds an inequality comparison expression."""
        return Expression(self, '!=', other)
    
    def __lt__(self, other: Any) -> 'Expression':
        """Builds a less-than comparison expression."""
        return Expression(self, '<', other)
    
    def __le__(self, other: Any) -> 'Expression':
        """Builds a less-than-or-equal comparison expression."""
        return Expression(self, '<=', other)
    
    def __gt__(self, other: Any) -> 'Expression':
        """Builds a greater-than comparison expression."""
        return Expression(self, '>', other)
    
    def __ge__(self, other: Any) -> 'Expression':
        """Builds a greater-than-or-equal comparison expression."""
        return Expression(self, '>=', other)
    
    def __invert__(self) -> 'Expression':
        """Negates the expression using SQL NOT."""
        return Expression(None, 'NOT', self)
    
    def like(self, pattern: str) -> 'Expression':
        """Builds a LIKE predicate expression."""
        return Expression(self, 'LIKE', pattern)

    def in_(self, items: Iterable[Any]) -> 'Expression':
        """Builds an IN predicate expression."""
        return Expression(self, 'IN', list(items))

    def not_in(self, items: Iterable[Any]) -> 'Expression':
        """Builds a NOT IN predicate expression."""
        return Expression(self, 'NOT IN', list(items))

    def _is_logical(self) -> bool:
        """Returns True when the operator is logical (AND, OR, NOT)."""
        return self.operator in {'AND', 'OR', 'NOT'}

    def _operand_to_sql(self, operand: Any) -> str:
        """Converts an operand to its SQL textual representation."""
        if isinstance(operand, Expression):
            return f"({operand.generate_clause()})"
        if hasattr(operand, 'parent_model') and operand.parent_model is not None:
            return f"{operand.parent_model.__tablename__}.{operand.name}"
        if hasattr(operand, 'name'):
            return str(operand.name)
        return str(operand)

    def generate_clause(self) -> str:
        """Generates a parameterized SQL predicate fragment.

        Returns:
            A SQL fragment that may contain ? placeholders.

        Raises:
            ValueError: If IN/NOT IN receives a non-iterable or empty iterable.
        """
        if self.operator == 'NOT':
            return f"NOT ({self._operand_to_sql(self.right)})"

        if self.operator in {'AND', 'OR'}:
            left_sql = self._operand_to_sql(self.left)
            right_sql = self._operand_to_sql(self.right)
            return f"{left_sql} {self.operator} {right_sql}"

        left_sql = self._operand_to_sql(self.left)

        if self.right is None:
            if self.operator == '=':
                return f"{left_sql} IS NULL"
            if self.operator == '!=':
                return f"{left_sql} IS NOT NULL"

        if self.operator in {'IN', 'NOT IN'}:
            if not isinstance(self.right, (list, tuple, set)):
                raise ValueError(f"Operator '{self.operator}' expects an iterable value")
            right_values = list(self.right)
            if not right_values:
                raise ValueError(f"Operator '{self.operator}' expects at least one value")
            placeholders = ", ".join("?" for _ in right_values)
            return f"{left_sql} {self.operator} ({placeholders})"

        return f"{left_sql} {self.operator} ?"

    def get_values(self) -> List[Any]:
        """Returns bind values in the same order as placeholders in generate_clause()."""
        if self.operator == 'NOT':
            if isinstance(self.right, Expression):
                return self.right.get_values()
            return []

        if self.operator in {'AND', 'OR'}:
            values: List[Any] = []
            if isinstance(self.left, Expression):
                values.extend(self.left.get_values())
            if isinstance(self.right, Expression):
                values.extend(self.right.get_values())
            return values

        if self.right is None and self.operator in {'=', '!='}:
            return []

        if self.operator in {'IN', 'NOT IN'}:
            return list(self.right)

        # Field instances are column references, not bind values
        if hasattr(self.right, 'parent_model'):
            return []

        return [self.right]
    
    def generate_join_clause(self) -> str:
        """Generates a SQL ON clause fragment where both sides are rendered as column references."""
        if self.operator in {'AND', 'OR'}:
            left_sql = self.left.generate_join_clause() if isinstance(self.left, Expression) else self._operand_to_sql(self.left)
            right_sql = self.right.generate_join_clause() if isinstance(self.right, Expression) else self._operand_to_sql(self.right)
            return f"{left_sql} {self.operator} {right_sql}"

        left_sql = self._operand_to_sql(self.left)
        right_sql = self._operand_to_sql(self.right)
        return f"{left_sql} {self.operator} {right_sql}"

    def to_sql(self) -> str:
        """Compatibility alias for generate_clause()."""
        return self.generate_clause()