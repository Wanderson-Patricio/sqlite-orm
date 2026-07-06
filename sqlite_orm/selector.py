from abc import ABC, abstractmethod

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


def compile_node(node) -> str:
    """Função utilitária para converter o argumento para string SQL."""
    if isinstance(node, Selector):
        return node.compile()
    
    # Se você passar a classe do Model inteira, ex: Count(User), converte para '*'
    if isinstance(node, type): 
        return "*"
    
    # Se for um atributo de modelo (ex: User.name) e for um descritor que tem 'name'
    if hasattr(node, 'name'):
        return node.name
    
    # Caso seja uma string crua ou outro tipo
    return str(node)