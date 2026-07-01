# SQLITE ORM - Um Wrapper para utilização simplificada do sqlite3

## Visão Geral da Arquitetura

O SQLiteORM é uma biblioteca de mapeamento objeto-relacional (ORM) desenvolvida para facilitar a interação com bancos de dados SQLite. Ele abstrai a complexidade das operações SQL, permitindo que os desenvolvedores trabalhem com objetos Python para realizar operações no banco de dados.

## Instalação

Para instalar o **SQLiteORM** no seu projeto, rode o seguinte comando no terminal:

```bash
pip install python-sqlite3-orm
```

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

      id = IntegerID()
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
       session = db.get_session(User)
   ```

   caso o desenvolvedor deseje que sejam exibidas as queries que estão sendo executadas, basta usar o método **debug** com o parâmetro ***enable*** definida como ***True***.

   ```python
   from sqlite_orm.database_manager import DatabaseContextManager, DBSession

   with DatabaseContextManager("example.db") as db:
       session = db.get_session(User).debug(enable=True)

   # Ou

   with DatabaseContextManager("example.db") as db:
       session = db.get_session(User)

       session.debug(enable=True, in_place=True)
   ```


- ### SELECT

1. **Configuração da Query**:
   - O desenvolvedor configura filtros, ordenação e outras opções usando `SessionOptions`.

   ```python
   from sqlite_orm.database_manager import DatabaseContextManager, DBSession

   with DatabaseContextManager("example.db") as db:
       session = db.get_session(User)

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

3. **Filtros no SELECT (recomendado: Expressions)**

    A forma recomendada para filtrar é utilizar **Expressions** diretamente nos campos do modelo, com operadores Python. Esse formato é mais legível combinável e simples de manter.

    ```python
    users = (
         session
         .select()
         .all()
         .where((User.age > 18) & (User.name.like("A%")))
         .to_model()
         .execute()
    )
    ```

    Todas as formas de filtro suportadas hoje:

    1. **Expression simples (recomendado)**
    ```python
    session.select().all().where(User.id == 1).execute()
    session.select().all().where(User.age >= 18).execute()
    session.select().all().where(User.name != "John").execute()
    ```

    2. **Expression composta com operadores lógicos (recomendado)**
    ```python
    session.select().all().where((User.age > 18) & (User.name.like("J%"))).execute()
    session.select().all().where((User.age < 18) | (User.name == "Admin")).execute()
    session.select().all().where(~(User.name.like("%teste%"))).execute()
    ```

    3. **LIKE, IN e NOT IN com Expression (recomendado)**
    ```python
    session.select().all().where(User.name.like("%John%")).execute()
    session.select().all().where(User.id.in_([1, 2, 3])).execute()
    session.select().all().where(User.id.not_in([4, 5])).execute()
    ```

    4. **Comparações com NULL (recomendado)**
    ```python
    session.select().all().where(User.name == None).execute()  # IS NULL
    session.select().all().where(User.name != None).execute()  # IS NOT NULL
    ```

    5. **Atalho por kwargs com igualdade**
    ```python
    session.select().all().where(id=1).execute()
    session.select().all().where(name="Alice").execute()
    ```

    6. **Modo legado com QueryFilter (compatibilidade)**
    ```python
    from sqlite_orm.query_filter import Equals, GreaterThan, Like, In, AND, OR

    session.select().all().where(id=Equals(1)).execute()
    session.select().all().where(age=GreaterThan(18)).execute()
    session.select().all().where(name=Like("%John%")).execute()
    session.select().all().where(id=In([1, 2, 3])).execute()

    session.select().all().where(
         OR(
             AND(name=Equals("John"), age=GreaterThan(18)),
             AND(name=Like("%Admin%"), age=GreaterThan(60))
         )
    ).execute()
    ```

    > [!TIP]
    > Para novos projetos e novas consultas, prefira Expressions.
    > QueryFilter, AND e OR continuam disponíveis para compatibilidade com código legado.

## Exemplos de Código

### Criação de Tabelas

```python
   from sqlite_orm.model import Model
   from sqlite_orm.field import ID, Integer, String
   from sqlite_orm import DatabaseContextManager, DBSession

   class User(Model):
      __tablename__ = "Users"

      id = IntegerID()
      name = String(max_length=100, nullable=False)
      cpf = String(max_length=11, nullable=False, unique=True)
      idade = Integer()

   with DatabaseContextManager("example.db") as db:
       session = db.get_session(User)
       session.create_table().execute()
   ```

### Deleção de Tabelas

```python
   from sqlite_orm.model import Model
   from sqlite_orm.field import ID, Integer, String
   from sqlite_orm import DatabaseContextManager, DBSession

   class User(Model):
      __tablename__ = "Users"

      id = IntegerID()
      name = String(max_length=100, nullable=False)
      cpf = String(max_length=11, nullable=False, unique=True)
      idade = Integer()

   with DatabaseContextManager("example.db") as db:
       session = db.get_session(User)
       session.drop_table().execute()
   ```

### Inserindo Dados

```python
from sqlite_orm.model import Model
from sqlite_orm.field import ID, String
from sqlite_orm import DatabaseContextManager, DBSession

class Product(Model):
    id = IntegerID()
    name = String(nullable=False)

with DatabaseContextManager("store.db") as db:
    session = db.get_session(Product)
    product = Product(name="Laptop")
    session.insert(product)
    id = session.execute() # Retorna o id do objeto inserido no banco de dados

    product = session.select() \
      .first() \
      .where(Product.id == id) \
      .to_model() \
      .execute()

    print(product.name) # Laptop
```

### Atualizando Dados

```python
with DatabaseContextManager("store.db") as db:
    session = db.get_session(Product)
    session.update() \
    .set(name = "Gaming Laptop") \
    .where(Product.id == 1) \
    .execute()
```

### Deletando Dados

```python
with DatabaseContextManager("store.db") as db:
    session = db.get_session(Product)
    session.delete() \
    .where(Product.id == 1) \
    .execute()
```