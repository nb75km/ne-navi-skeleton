# ---- Database helpers ----
export DATABASE_URL ?= postgresql+psycopg2://app:app@localhost:5432/app

# --- Celery / Alembic helpers ---------------------------------
db-upgrade:
	@docker compose exec chat alembic upgrade head

db-reset:
	@docker compose exec postgres \
		psql -U app -d app \
		-c "DROP SCHEMA IF EXISTS chat CASCADE; DROP SCHEMA IF EXISTS minutes CASCADE;"
	@docker compose exec chat alembic stamp base
	@docker compose exec chat alembic upgrade head

etl-run:
	@docker compose exec celery python - <<'PY'
from shared.etl_dify import sync_dify; sync_dify.delay()
print("Triggered ETL task")
PY