# mosquito-colector-services

Coletor Python MQTT executado continuamente em Docker. As mensagens são salvas localmente no volume:

```text
logs/AAAA/MM/DD.json
```

O arquivo `secrets.h` contém credenciais locais e é ignorado pelo Git. Nunca remova `secrets.h` do `.gitignore` nem publique credenciais no repositório.

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
