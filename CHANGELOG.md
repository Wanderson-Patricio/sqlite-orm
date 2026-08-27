# Changelog

Todas as mudanças notáveis desse projeto serão documentadas nesse arquivo.

> Ao adicionar uma nova mudança escreva acima da primeira mudança apresentada no arquivo (a mais recente) para que as mudanças mais recentes apareçam sempre no início do arquivo.


## 2026-08-03 (@Wanderson-Patricio / Wanderson Faustino Patricio)
### Adicionado

- Incluída a opção de realizar joins, permitindo que sejam feitas interações entre tabelas.

- Incluído o método group_by.

- Incluído novos selectors: SUM, AVG, CONCAT.

### Corrigido

- Corrigido como eram feitos os retornos do método select para que os campos (Field) também pudessem receber de qual model eles são. Logo ao invés de aparecer `SELECT id ...` agora aparecerá `SELECT Users.id ...`. Essa mudança também foi implementada no método where.


## 2026-07-31 (@Wanderson-Patricio / Wanderson Faustino Patricio)
### Adicionado

- Incluída a opção de utilizar os campos do modelo para poder fazer a ordenação, além de porder escolher se a ordenação será crescente ou decrescente.

- Alterado o atributo *foreign_key* dos campos para que seja utilizado o modelo e o campo da definição da chave estrangeira ao invés de strings, reduzindo a manutenção de código caso o nome da tabela ou do campo da tabela estrangeira seja alterado.


### Corrigido

- Alterado o retorno do método ***INSERT*** no *db_session* para que seja retornado os ids em string (UUID), além dos ids numéricos.

- Corrigidos alguns métodos *__validate__* nos campos principais.