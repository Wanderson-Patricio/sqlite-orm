# SQLITE ORM - Um Wrapper para utilização simplificada do sqlite3

## Visão Geral da Arquitetura

O SQLiteORM é uma biblioteca de mapeamento objeto-relacional (ORM) desenvolvida para facilitar a interação com bancos de dados SQLite. Ele abstrai a complexidade das operações SQL, permitindo que os desenvolvedores trabalhem com objetos Python para realizar operações no banco de dados.

### Componentes Principais

1. **`clauses.py`**:
   - Define as cláusulas SQL, como `WHERE`, `ORDER BY`, `LIMIT` e `OFFSET`.
   - Contém classes como `QueryClauses` e `ClauseGenerator` para gerar partes específicas de uma query SQL.

2. **`database_manager.py`**:
   - Gerencia conexões com o banco de dados SQLite.
   - Fornece um gerenciador de contexto para garantir que as conexões sejam abertas e fechadas corretamente.

3. **`db_session.py`**:
   - Gerencia sessões de interação com o banco de dados.
   - Permite configurar filtros, ordenação e outras opções para consultas.

4. **`field.py`**:
   - Define os tipos de campos disponíveis para os modelos, como `Integer` e `String`.
   - Implementa validações e o protocolo de descritores para gerenciar o acesso aos dados.

5. **`model.py`**:
   - Define a metaclasse `ModelMeta` para processar atributos de classe e configurar metadados, como o nome da tabela e os campos.
   - Permite que os modelos representem tabelas no banco de dados.

## Fluxo de uma query

1. **Definição de Campos**
   - O desenvolvedor pode definir campos a serem utilizados dentro de seus modelos. Ao estruturar uma tabela no banco de dados, o desenvolvedor deve definir o nome do campo e as suas especificidades. Por exemplo, ao definir um tabela "Users" com *id*, *nome*, *cpf* e *idade*, poderia ser utilizado a seguinte query **SQL**:

   ```sql
   CREATE TABLE Users (
      id INTEGER PRIMARY KEY,
      nome VARCHAR(100) NOT NULL,
      cpf VARCHAR(11) NOT NULL UNIQUE,
      idade INTEGER
   );
   ```

   Os campos (Integer, Varchar, ...) foram abstraídos para a classe ***Field***.

   ```python
   class Field(ABC):
    """
    Base class for all field types in the ORM.
    """

      def __init__(
         self,
         *,
         type: str, 
         primary_key: bool = False, 
         nullable: bool = True, 
         unique: bool = False
      ) -> None:

      ...
   ```

   Alguns campos mais comuns foram definidos no pacote ***field***, sendo eles:

   - **Integer**: Tipo genérico para números inteiros.
   - **ID**: Um campo inteiro especial usado como chave primária única.
   - **BigInteger**: Um campo para números inteiros grandes.
   - **Decimal**: Representa números decimais com precisão e escala configuráveis.
   - **String**: Um campo para strings com comprimento máximo configurável.
   - **Boolean**: Representa valores booleanos (`True` ou `False`).
   - **Float**: Um campo para números de ponto flutuante.
   - **Text**: Um campo para strings longas.
   - **Blob**: Representa dados binários, como imagens ou arquivos.
   - **DateTime**: Um campo para armazenar data e hora no formato ISO 8601.
   - **Date**: Representa apenas a data no formato ISO 8601.
   - **Time**: Representa apenas o horário no formato ISO 8601.

   O usuário pode criar novos tipos de dados.

   ```python
   from sqlite_orm.field import Field

   class NewField(Field):
      def __init__(self, *args, **kwargs) ->  None:
         super().__init__(type='NEW_FIELD', **kwargs)

      def __validate__(self, value):
         # Implementação do validador
         raise NotImplementedError()
   ```

   > [!INFO]
   > Para a criação de novos campos, é obrigatório a implementação de um validador, que indica se o valor fornecido na criação do modelo é válido.

2. **Definição do Modelo**:

   - O desenvolvedor define uma classe que herda de `Model` e especifica os campos como instâncias de `Field`. Ademais, é necessário ser indicado o nome da tabela com o campo *'__tablename__'*.

   ```python
   from sqlite_orm.model import Model
   from sqlite_orm.field import ID, Integer, String

   class User(Model):
      __tablename__ = "Users"

      id = ID()
      name = String(max_length=100, nullable=False)
      cpf = String(max_length=11, nullable=False, unique=True)
      idade = Integer()
   ```

   - Para criar uma nova instância de um modelo, basta seguir o processo de criação de um **dataclass**.

   ```python
   user = User(id=1, nome='Fulano da Silva', cpf='12345678900', idade =20)
   ```

3. **Criação da Sessão**:
   - Uma instância de `DatabaseContextManager` é usada para gerenciar a conexão com o banco de dados.

   ```python
   from sqlite_orm.database_manager import DatabaseContextManager, DBSession

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db)
   ```

   caso o desenvolvedor deseje que sejam exibidas as queries que estão sendo executadas, basta usar o método **debug** com o parâmetro ***enable*** definida como ***True***.

   ```python
   from sqlite_orm.database_manager import DatabaseContextManager, DBSession

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db).debug(enable=True)

   # Ou

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db)

       session.debug(enable=True, in_place=True)
   ```


- ### SELECT

1. **Configuração da Query**:
   - O desenvolvedor configura filtros, ordenação e outras opções usando `SessionOptions`.

   ```python
   from sqlite_orm.database_manager import DatabaseContextManager, DBSession

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db)

       session = session.select().all()
   ```

   para uma query **SELECT** é preciso indicar se serão retornados vários objetos (lista) ou apenas um objeto (tupla ou *Model*).

   ```python
   session = session.select().all()
   # OU
   session = session.select().first()
   ```

   Poder ser escolhido pelo usuário se o retorno da função será dado em uma tupla ou como uma instância do modelo criado anteriormente, através do método **to_model()**.

   **Exemplos de retorno:**
   ```python
   session = session.select().all()
   # [(1, 'Fulando da Silva', '12345678900', 20)]
   
   session = session.select().first()
   # (1, 'Fulando da Silva', '12345678900', 20)
   
   session = session.select().all().to_model()
   # [<User (id=1, nome='Fulando da Silva', cpf='12345678900', idade=20)>]
   
   session = session.select().first().to_model()
   # <User (id=1, nome='Fulando da Silva', cpf='12345678900', idade=20)>
   ```

2. **Execução da Query**:
   - Para que a query seja executada, é necessário utilizar o método execute.

   ```python
   results = session.select().all().to_model().execute()
   for user in results:
       print(user.name)
   ```

3. **Query Filters**
   - Para filtrar dados através de campos específicos, podem ser utilizados ***Query Filters***.

   ```python
   from sqlite_orm.query_filter import *
   ```

   Os filtros configurados são:

   - **Equals**: Verifica se o valor de um campo é igual ao valor especificado.
     ```python
     session.where(name = Equals("John"))
     ```
   - **NotEquals**: Verifica se o valor de um campo é diferente do valor especificado.
     ```python
     session.where(name = NotEquals("John"))
     ```
   - **GreaterThan**: Verifica se o valor de um campo é maior que o valor especificado.
     ```python
     session.where(age = GreaterThan(18))
     ```
   - **GreaterThanOrEqual**: Verifica se o valor de um campo é maior ou igual ao valor especificado.
     ```python
     session.where(age = GreaterThanOrEqual(18))
     ```
   - **LessThan**: Verifica se o valor de um campo é menor que o valor especificado.
     ```python
     session.where(age = LessThan(18))
     ```
   - **LessThanOrEqual**: Verifica se o valor de um campo é menor ou igual ao valor especificado.
     ```python
     session.where(age = LessThanOrEqual(18))
     ```
   - **Like**: Verifica se o valor de um campo corresponde a um padrão especificado (usando curingas como `%`).
     ```python
     session.where(name = Like("%John%"))
     ```
   - **In**: Verifica se o valor de um campo está contido em uma lista de valores.
     ```python
     session.where(id = In([1, 2, 3]))
     ```

   Também é possível fazer associações de filtros, através da combinação com os *query_filters* **AND** e **OR**.
   Por exemplo, para filtrar pela expressão:

   ```sql
   WHERE (name = 'John' AND age < 18) OR (name LIKE '%John%' AND age >= 18)
   ```

   será utilizada a combinação:

   ```python
   session.where(
      OR(
         AND(name = Equals('John'), age = LessThan(18)),
         AND(name = Like('%John%'), age = GreaterThanOrEqual(18))
      )
   )
   ```

## Exemplos de Código

### Criação de Tabelas

```python
   from sqlite_orm.model import Model
   from sqlite_orm.field import ID, Integer, String
   from sqlite_orm import DatabaseContextManager, DBSession

   class User(Model):
      __tablename__ = "Users"

      id = ID()
      name = String(max_length=100, nullable=False)
      cpf = String(max_length=11, nullable=False, unique=True)
      idade = Integer()

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db)
       session.create_table().execute()
   ```

### Deleção de Tabelas

```python
   from sqlite_orm.model import Model
   from sqlite_orm.field import ID, Integer, String
   from sqlite_orm import DatabaseContextManager, DBSession

   class User(Model):
      __tablename__ = "Users"

      id = ID()
      name = String(max_length=100, nullable=False)
      cpf = String(max_length=11, nullable=False, unique=True)
      idade = Integer()

   with DatabaseContextManager("example.db") as db:
       session = DBSession(User, db)
       session.drop_table().execute()
   ```

### Inserindo Dados

```python
from sqlite_orm.query_filter import Equals
from sqlite_orm.model import Model
from sqlite_orm.field import ID, String
from sqlite_orm import DatabaseContextManager, DBSession

class Product(Model):
    id = ID()
    name = String(nullable=False)

with DatabaseContextManager("store.db") as db:
    session = DBSession(User, db)
    product = Product(name="Laptop")
    session.insert(product)
    id = session.execute() # Retorna o id do objeto inserido no banco de dados

    product = session.select() \
      .first() \
      .where(id = Equals(id)) \
      .to_model() \
      .execute()

    print(product.name) # Laptop
```

### Atualizando Dados

```python
with DatabaseContextManager("store.db") as db:
    session = DBSession(Product, db)
    session.update() \
         .set(name = "Gaming Laptop") \
         .where(id = Equals(1)) \
         .execute()
```

### Deletando Dados

```python
with DatabaseContextManager("store.db") as db:
    session = DBSession(Product, db)
    session.delete() \
         .where(id = Equals(1)) \
         .execute()
```