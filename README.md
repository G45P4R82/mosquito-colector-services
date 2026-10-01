# mosquito-colector-services

Coletor Python MQTT executado continuamente em Docker. As mensagens são salvas localmente no volume:

```text
logs/AAAA/MM/DD.json
```

O arquivo `secrets.h` contém credenciais locais e é ignorado pelo Git. Nunca remova `secrets.h` do `.gitignore` nem publique credenciais no repositório.

As credenciais MQTT ficam em `users/users.txt`, uma por linha no formato `usuario:senha`. O coletor cria automaticamente um subscribe em `sensores/<usuario>/#` para cada linha.

## Operação no VPS

```bash
make configure
make up
make logs
make status
```

Para adicionar ou remover sensores, edite `users/users.txt` e execute `make restart`.

## Executar

```bash
docker compose up -d --build
```

## Acompanhar

```bash
docker compose logs -f mqtt-log-collector
```

## Parar

```bash
docker compose down
```
