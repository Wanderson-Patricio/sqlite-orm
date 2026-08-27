from typing import Any, Optional


class JoinGenerator:
    @staticmethod
    def generate(join_option: Optional[Any] = None) -> str:
        if not join_option or not join_option.models:
            return ""
        
        join_str = ""
        for join_model, join_type in zip(join_option.models, join_option.types):
            join_str += f"{join_type} JOIN {join_model.__tablename__} "

        join_str += f"ON {join_option.expression.generate_join_clause()}"
        return join_str