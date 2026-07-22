.PHONY: up down logs ingest test

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f app

ingest:
	docker compose exec app python -m app.ingest

test:
	pytest -q

