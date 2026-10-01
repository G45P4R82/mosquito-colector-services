.PHONY: configure up logs status down restart check

configure:
	@test -f users/users.txt || (printf '%s\n' 'ERRO: crie users/users.txt antes de configurar.'; exit 1)
	docker compose build
	docker compose run --rm mqtt-log-collector main.py --validate-users

up:
	docker compose up -d --build

logs:
	docker compose logs -f mqtt-log-collector

status:
	docker compose ps
	docker compose run --rm mqtt-log-collector main.py --validate-users

down:
	docker compose down

restart:
	docker compose up -d --build --force-recreate

check:
	docker compose config --quiet
	docker compose run --rm mqtt-log-collector main.py --validate-users
