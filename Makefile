up-db:
	if docker network ls --format "{{.Name}}" | grep bar_network; then \
		echo "Network 'bar_network' already exists"; \
	else \
		echo "Creating network 'bar_network'..."; \
		docker network create bar_network; \
	fi

	docker compose build
	docker compose down
	docker compose up -d

run:
	cd src && uv run main.py

up: up-db run

stop:
	docker compose stop

test:
	PYTHONPATH=src:tests pytest

format:
	uv run ruff check --select I,F401 --fix
	uv run ruff format

down:
	docker compose down
	docker volume prune -a -f

prune:
	make stop
	docker compose down
	docker system prune -a -f
	docker volume prune -a -f
