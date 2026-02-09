# 🚀 Czech MedAI - Production Deployment Guide

Kompletní návod pro nasazení Czech MedAI API do production prostředí.

---

## 📋 Předpoklady

### Systémové Požadavky

- **Docker**: ≥24.0.0
- **Docker Compose**: ≥2.20.0
- **RAM**: ≥4GB (doporučeno 8GB)
- **CPU**: ≥2 cores (doporučeno 4 cores)
- **Disk**: ≥20GB volného místa

### Externí Služby

- **Supabase** (PostgreSQL + pgvector): https://supabase.com
- **Redis Cloud** (optional): https://redis.com/cloud
- **LangSmith** (tracing): https://smith.langchain.com
- **Sentry** (monitoring, optional): https://sentry.io

---

## 🔧 Krok 1: Environment Configuration

### 1.1 Vytvořit Production Environment File

```bash
# Copy template
cp .env.production.example .env.production

# Edit with production values
nano .env.production
```

### 1.2 Povinné Proměnné

```bash
# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:5432/czech_medai
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_production_key

# Redis Cache
REDIS_URL=redis://redis:6379/0  # Docker Compose
# OR Redis Cloud:
# REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345

# CORS (restrict to your frontend)
CORS_ORIGINS=https://your-frontend.com,https://app.your-domain.com

# OpenAI (embeddings)
OPENAI_API_KEY=sk-your_production_key

# LangSmith (tracing)
LANGSMITH_API_KEY=lsv2_pt_your_production_key
LANGSMITH_PROJECT=czech-medai-production
```

### 1.3 Volitelné Proměnné

```bash
# Sentry (error monitoring)
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
SENTRY_ENVIRONMENT=production

# JWT (future authentication)
JWT_SECRET=your_random_256_bit_secret
```

---

## 🐳 Krok 2: Docker Deployment

### 2.1 Build Docker Image

```bash
# Build production image
docker build -t czech-medai-api:latest .

# Verify image size (<500MB)
docker images czech-medai-api:latest
```

### 2.2 Start Services with Docker Compose

```bash
# Start all services (API + Redis + PostgreSQL)
docker-compose up -d

# Check logs
docker-compose logs -f api

# Verify health
curl http://localhost:8000/health
```

### 2.3 Run Database Migrations

```bash
# Run migrations inside container
docker-compose exec api python -m alembic upgrade head

# OR manually with psql
docker-compose exec postgres psql -U postgres -d czech_medai -f /migrations/003_guidelines_schema.sql
```

---

## 📊 Krok 3: Monitoring Setup

### 3.1 LangSmith Tracing

1. Vytvořit projekt na https://smith.langchain.com
2. Získat API key
3. Nastavit v `.env.production`:
   ```bash
   LANGSMITH_API_KEY=lsv2_pt_your_key
   LANGSMITH_PROJECT=czech-medai-production
   LANGSMITH_TRACING=true
   ```

### 3.2 Sentry Error Monitoring (Optional)

1. Vytvořit projekt na https://sentry.io
2. Získat DSN
3. Nastavit v `.env.production`:
   ```bash
   SENTRY_DSN=https://your_dsn@sentry.io/project_id
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1
   ```

### 3.3 Log Aggregation

**Structured JSON logs** jsou v `/app/logs/czech-medai.log` (rotace denně, 30 dní retention).

**Integrace s ELK Stack**:
```bash
# Filebeat configuration
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /app/logs/czech-medai.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["https://your-elk-cluster:9200"]
```

---

## 🔒 Krok 4: Security Checklist

### 4.1 CORS Configuration

✅ Restrict `CORS_ORIGINS` to your frontend domains:
```bash
CORS_ORIGINS=https://your-frontend.com,https://app.your-domain.com
```

### 4.2 Rate Limiting

✅ Default: 10 requests/minute per IP
```bash
RATE_LIMIT_PER_MINUTE=10
```

### 4.3 HTTPS/TLS

✅ Use reverse proxy (Nginx, Caddy) for TLS termination:
```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4.4 Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 📈 Krok 5: Performance Tuning

### 5.1 Uvicorn Workers

```bash
# .env.production
API_WORKERS=4  # Number of CPU cores
```

### 5.2 Redis Memory Limit

```bash
# docker-compose.yml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 5.3 Database Connection Pool

```bash
# .env.production
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
```

---

## 🧪 Krok 6: Load Testing

### 6.1 Run Benchmark

```bash
# Start API
docker-compose up -d

# Run load test
./tests/load_tests/benchmark.sh
```

### 6.2 Performance Targets

- ✅ **100+ concurrent users**
- ✅ **<5s p95 latency**
- ✅ **<1% error rate**
- ✅ **>50 RPS throughput**

### 6.3 Analyze Results

```bash
# Open HTML report
open tests/load_tests/results/benchmark_YYYYMMDD_HHMMSS.html
```

---

## 🔄 Krok 7: Continuous Deployment

### 7.1 GitHub Actions (Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t czech-medai-api:${{ github.sha }} .

      - name: Push to registry
        run: |
          docker tag czech-medai-api:${{ github.sha }} your-registry/czech-medai-api:latest
          docker push your-registry/czech-medai-api:latest

      - name: Deploy to server
        run: |
          ssh user@your-server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## 🆘 Troubleshooting

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Missing environment variables → Check .env.production
# 2. Database connection failed → Verify DATABASE_URL
# 3. Redis unavailable → Check REDIS_URL
```

### High Latency

```bash
# Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace_hits

# Check database query performance
docker-compose exec postgres psql -U postgres -d czech_medai -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Memory Issues

```bash
# Check container memory usage
docker stats

# Increase Redis memory limit
# Edit docker-compose.yml: --maxmemory 512mb
```

---

## 📞 Support

- **Documentation**: `README.md`, `CLAUDE.md`
- **Issues**: GitHub Issues
- **Email**: support@your-domain.com

---

## 📝 Changelog

### v0.1.0 (2026-02-06)
- ✅ Initial production deployment
- ✅ Docker containerization
- ✅ Redis caching
- ✅ Structured logging
- ✅ Load testing
- ✅ Security hardening
