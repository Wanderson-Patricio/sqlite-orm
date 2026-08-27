from abc import ABC, abstractmethod

from .field import Field

class Selector(ABC):
    """Classe base para funções e campos selecionáveis."""
    
    @abstractmethod
    def compile(self) -> str:
        pass

    def As(self, alias: str) -> 'Alias':
        return Alias(self, alias)


class Alias(Selector):
    def __init__(self, element, alias: str):
        self.element = element
        self.alias = self.__validate_alias(alias)

    def __validate_alias(self, alias: str):
        if not isinstance(alias, str) or not alias:
            raise ValueError("Alias must be a non-empty string.")
        
        return alias.lower().strip().replace(" ", "_")


    def __str__(self):
        return f"{self.element} AS {self.alias}"

    def compile(self) -> str:
        # Envolve o alias em aspas duplas para suportar espaços no nome
        return f'{compile_node(self.element)} AS "{self.alias}"'


class Count(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"COUNT({compile_node(self.element)})"


class Distinct(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"DISTINCT {compile_node(self.element)}"
    

class Max(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"MAX({compile_node(self.element)})"
    

class Min(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"MIN({compile_node(self.element)})"    


class Sum(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"SUM({compile_node(self.element)})"


class Mean(Selector):
    def __init__(self, element):
        self.element = element

    def compile(self) -> str:
        return f"AVG({compile_node(self.element)})"


class Concat(Selector):
    def __init__(self, *elements):
        self.elements = elements

    def compile(self) -> str:
        compiled_elements = ", ".join(compile_node(el) for el in self.elements)
        return f"CONCAT({compiled_elements})"


def compile_node(node, with_alias: bool = False) -> str:
    """Função utilitária para converter o argumento para string SQL."""
    if isinstance(node, Selector):
        return node.compile()
    
    # Se você passar a classe do Model inteira, ex: Count(User), converte para '*'
    if isinstance(node, type): 
        return "*"
    
    # Se for um atributo de modelo (ex: User.name) e for um descritor que tem 'name'
    if isinstance(node, Field) and hasattr(node, 'name'):
        col = f"{node.parent_model.__tablename__}.{node.name}"
        if with_alias:
            return f'{col} AS "{col}"'
        return col
    
    # Caso seja uma string crua ou outro tipo
    return str(node)