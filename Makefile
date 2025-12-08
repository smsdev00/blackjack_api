# Load environment variables from .env file if it exists
-include .env

# Makefile
.PHONY: help build up down logs restart api clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Inicia todos los contenedores como daemon
	docker compose up -d

down: ## Detiene todos los servicios
	docker compose down

ps: ## Lista los contenedores en ejecucion
	docker ps

clean: ## Limpia contenedores, imagenes y volumenes
	docker compose down -v
	docker system prune -f

logs: ## Muestra los logs de todos los servicios
	docker compose logs -f

logs-api: ## Muestra los logs de la API
	docker compose logs -f api

logs-front: ## Muestra los logs del frontend
	docker compose logs -f front

logs-db: ## Muestra los logs de la base de datos
	docker compose logs -f db

restart: ## Reinicia todos los servicios
	docker compose restart

rebuild: ## Fuerza reconstruccion de todos los contenedores
	docker compose up -d --build --force-recreate

rebuild-api: ## Fuerza reconstruccion del container api
	docker compose up -d --build --force-recreate api

rebuild-front: ## Fuerza reconstruccion del container front
	docker compose up -d --build --force-recreate front

api-shell: ## Conecta a la shell de la API
	docker compose exec api sh

front-shell: ## Conecta a la shell del frontend
	docker compose exec front sh

db-shell: ## Conecta a MySQL shell
	docker compose exec db mysql -u$(DB_USER) -p$(DB_PASSWORD) $(DB_DATABASE)

db-backup: ## Realiza un backup de la base de datos
	@mkdir -p backups
	docker compose exec -e MYSQL_PWD="$(DB_PASSWORD)" db mysqldump -u"$(DB_USER)" "$(DB_DATABASE)" > backups/db_backup_$(DB_DATABASE)_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup creado en backups/"

db-restore: ## Restaura backup (usar: make db-restore FILE=backups/archivo.sql)
	docker compose exec -T -e MYSQL_PWD="$(DB_PASSWORD)" db mysql -u"$(DB_USER)" "$(DB_DATABASE)" < $(FILE)

test-api: ## Prueba la API (health check)
	curl -s http://localhost:$(API_PORT)/ | python -m json.tool

dev: ## Modo desarrollo (logs visibles)
	docker compose up

dev-build: ## Modo desarrollo con rebuild
	docker compose up --build

stop-api: ## Detiene solo la API
	docker compose stop api

stop-front: ## Detiene solo el frontend
	docker compose stop front

stop-db: ## Detiene solo la base de datos
	docker compose stop db

status: ## Muestra el estado de los servicios
	docker compose ps
