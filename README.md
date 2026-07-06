# AI Service

AI Service la service rieng cho phan AI cua he thong thuong mai dien tu mat hang cong nghe.

Huong trien khai tuan 1:

- FastAPI lam API server.
- `data/products.json` lam data mau khi backend chua co database.
- HTTP sync la cach dong bo san pham chinh trong giai doan dau.
- Alembic migration quan ly schema database cho AI Service.
- RabbitMQ contract duoc thiet ke truoc de sau nay nang cap thanh event-driven.

## Kien Truc

```txt
Backend Catalog Service
        |
        | HTTP sync product data
        v
AI Service - FastAPI
        |
        v
AI Database - PostgreSQL
```

Tuong lai co the bo sung RabbitMQ:

```txt
Catalog Service
        |
        | publish product.created / product.updated / product.deleted
        v
RabbitMQ
        |
        v
AI Service consumer
        |
        v
AI Database
```

## Cau Truc Project

```txt
ai-service/
  app/
    main.py
    routes/
    schemas/
    services/
    db/
    core/
  data/
    products.json
  docs/
  migrations/
  requirements.txt
  alembic.ini
```

## Cai Dat

Chay tai thu muc project:

```powershell
cd C:\Users\Lenovo\Documents\Codex\2026-06-30\b\work\ai-service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Neu PowerShell chan activate `.venv`, chay:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Chay FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

Swagger UI:

```txt
http://localhost:8000/docs
```

## Test API

### Health

```powershell
curl http://localhost:8000/api/v1/ai/health
```

Ket qua mong doi:

```json
{
  "status": "ok",
  "service": "ai-service"
}
```

### Get Products

```powershell
curl http://localhost:8000/api/v1/ai/products
```

Ket qua mong doi:

```txt
total = 20
```

### Sync Product

Backend se goi API nay khi them hoac sua san pham.

```powershell
curl -X POST http://localhost:8000/api/v1/ai/products/sync `
  -H "Content-Type: application/json" `
  -d "{\"product_id\":\"test-001\",\"name\":\"Test Product\",\"category\":\"laptop\",\"brand\":\"Test\",\"price\":1000000,\"description\":\"Test sync product\",\"specs\":{\"ram\":\"16GB\"},\"tags\":[\"test\"],\"image_url\":\"https://example.com/test.jpg\",\"is_active\":true}"
```

Ket qua mong doi:

```json
{
  "message": "Product synced successfully",
  "product_id": "test-001",
  "action": "created"
}
```

Neu goi lai cung `product_id`, `action` se la:

```txt
updated
```

### Deactivate Product

Backend se goi API nay khi xoa hoac an san pham.

```powershell
curl -X PATCH http://localhost:8000/api/v1/ai/products/test-001/deactivate
```

Ket qua mong doi:

```json
{
  "message": "Product deactivated successfully",
  "product_id": "test-001"
}
```

### Search

```powershell
curl -X POST http://localhost:8000/api/v1/ai/search `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"laptop ram 16gb hoc lap trinh\",\"limit\":5}"
```

Ket qua mong doi:

```txt
Tra ve danh sach laptop phu hop, co score keyword.
```

## Migration

Project da co Alembic migration dau tien tao bang:

```txt
ai_products
```

Chay migration khi PostgreSQL da san sang:

```powershell
alembic upgrade head
```

Huong dan chi tiet:

```txt
docs/MIGRATIONS.md
```

## RabbitMQ

Tuan 1 chua can code consumer RabbitMQ. Project da co event contract de backend va AI thong nhat truoc.

```txt
docs/RABBITMQ_EVENT_CONTRACT.md
```

Thong tin chinh:

```txt
Exchange: product.events
Type: topic
Queue: ai.product.events
Routing keys: product.created, product.updated, product.deleted
```

## Tai Lieu Chinh

```txt
docs/ARCHITECTURE.md
docs/API_CONTRACT.md
docs/PRODUCT_DATA_CONTRACT.md
docs/DATABASE_SCHEMA_DRAFT.sql
docs/BACKEND_DISCUSSION_CHECKLIST.md
```
