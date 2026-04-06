Create .env file, and put variables like that

```
POSTGRES_USER=Admin
POSTGRES_PASSWORD=SecurePassword123
POSTGRES_DB=main

POSTGRES_IMAGE=17-alpine

SECRET_KEY=SECURE_KEY
DEBUG=True
```

Launch

```bash
docker compose up --build -d
```

Run migrations

```bash
docker compose exec web python manage.py migrate
```

Load fixtures

```bash
docker compose exec web python manage.py loaddata apps/users/fixtures/users.json
docker compose exec web python manage.py loaddata apps/product/fixtures/products.json
docker compose exec web python manage.py loaddata apps/product/fixtures/carts.json
```

docs API

[http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/) 
