# Tài Liệu Vận Hành Odoo 19

## 1. QUẢN LÝ SERVICE ODOO

### 1.1. Khởi động Odoo

#### Sử dụng Docker Compose
```bash
# Khởi động tất cả services
cd /otp/odoo19
docker-compose up -d

# Khởi động chỉ Odoo service
docker-compose up -d odoo

# Xem logs khi khởi động
docker-compose up odoo
```

#### Sử dụng Systemd Service
```bash
# Khởi động service
sudo systemctl start odoo19

# Khởi động và enable auto-start
sudo systemctl enable --now odoo19

# Kiểm tra trạng thái
sudo systemctl status odoo19
```

### 1.2. Dừng Odoo

#### Docker Compose
```bash
# Dừng tất cả services
docker-compose down

# Dừng chỉ Odoo
docker-compose stop odoo

# Dừng và xóa containers
docker-compose down --remove-orphans
```

#### Systemd Service
```bash
# Dừng service
sudo systemctl stop odoo19

# Disable auto-start
sudo systemctl disable odoo19
```

#### Kill process 
```bash
# Tìm PID của Odoo
ps aux | grep odoo

# Kill graceful
sudo kill -TERM <PID>

# Force kill (chỉ khi cần thiết)
sudo kill -9 <PID>
```

### 1.3. Khởi động lại (Restart)

```bash
# Docker Compose
docker-compose restart odoo

# Systemd
sudo systemctl restart odoo19

# Restart với rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 2. KIỂM TRA TRẠNG THÁI HỆ THỐNG

### 2.1. Kiểm tra Service Status

```bash
# Docker containers
docker-compose ps

# System services
sudo systemctl status odoo19
sudo systemctl status postgresql
sudo systemctl status nginx

# Process monitoring
ps aux | grep -E "(odoo|postgres|nginx)"

# Port listening
netstat -tulpn | grep -E ":(8069|5432|80|443)"
```

### 2.2. Health Check Script

```bash
#!/bin/bash
# /opt/odoo19/scripts/health-check.sh

echo "=== Odoo 19 Health Check - $(date) ==="

# Check Docker containers
echo "1. Docker Containers:"
docker-compose ps

# Check HTTP response
echo "2. HTTP Response:"
curl -I http://localhost:8069/web/health 2>/dev/null | head -1

# Check database connection
echo "3. Database Connection:"
docker-compose exec db pg_isready -h localhost -p 5432

# Check disk space
echo "4. Disk Usage:"
df -h /opt/odoo19

# Check memory usage
echo "5. Memory Usage:"
free -h

# Check logs for errors (last 10 lines)
echo "6. Recent Errors:"
docker-compose logs odoo --tail=10 | grep -i error

echo "=== Health Check Completed ==="
```

### 2.3. Performance Monitoring

```bash
# CPU và Memory usage của Odoo
docker stats --no-stream odoo19_odoo_1

# Database performance
docker-compose exec db psql -U odoo -c "
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"

# Connection count
docker-compose exec db psql -U odoo -c "
SELECT count(*) as connection_count FROM pg_stat_activity;
"
```

## 3. QUẢN LÝ DATABASE

### 3.1. Backup Database

```bash
#!/bin/bash
# /opt/odoo19/scripts/backup-db.sh

DB_NAME="odoo19_production"
BACKUP_DIR="/opt/odoo19/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup with compression
docker-compose exec db pg_dump -U odoo -h localhost $DB_NAME | gzip > $BACKUP_DIR/odoo_backup_$DATE.sql.gz

# Keep only last 7 days backups
find $BACKUP_DIR -name "odoo_backup_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: odoo_backup_$DATE.sql.gz"
```

### 3.2. Restore Database

```bash
#!/bin/bash
# /opt/odoo19/scripts/restore-db.sh

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME="odoo19_production"

# Stop Odoo
docker-compose stop odoo

# Drop existing database
docker-compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# Create new database
docker-compose exec db psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER odoo;"

# Restore from backup
gunzip -c $BACKUP_FILE | docker-compose exec -T db psql -U odoo -h localhost $DB_NAME

# Start Odoo
docker-compose start odoo

echo "Database restored from $BACKUP_FILE"
```

### 3.3. Database Maintenance

```bash
# VACUUM và ANALYZE
docker-compose exec db psql -U odoo -d odoo19_production -c "VACUUM ANALYZE;"

# Reindex database
docker-compose exec db psql -U odoo -d odoo19_production -c "REINDEX DATABASE odoo19_production;"

# Check database size
docker-compose exec db psql -U odoo -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database 
WHERE datname = 'odoo19_production';
"
```

## 4. LOG MANAGEMENT

### 4.1. Xem Logs

```bash
# Docker logs - realtime
docker-compose logs -f odoo

# Docker logs - last 100 lines
docker-compose logs --tail=100 odoo

# System logs
sudo journalctl -u odoo19 -f

# Nginx logs
sudo tail -f /var/log/nginx/odoo_access.log
sudo tail -f /var/log/nginx/odoo_error.log

# PostgreSQL logs
docker-compose logs --tail=50 db
```

### 4.2. Log Rotation Script

```bash
#!/bin/bash
# /opt/odoo19/scripts/rotate-logs.sh

LOG_DIR="/opt/odoo19/logs"
MAX_SIZE="100M"
DAYS_TO_KEEP=30

# Rotate Odoo logs
if [ -f "$LOG_DIR/odoo.log" ]; then
    if [ $(stat -f%z "$LOG_DIR/odoo.log" 2>/dev/null || stat -c%s "$LOG_DIR/odoo.log") -gt $(echo $MAX_SIZE | numfmt --from=iec) ]; then
        mv "$LOG_DIR/odoo.log" "$LOG_DIR/odoo.log.$(date +%Y%m%d_%H%M%S)"
        touch "$LOG_DIR/odoo.log"
        chown odoo:odoo "$LOG_DIR/odoo.log"
        
        # Restart Odoo to use new log file
        docker-compose restart odoo
    fi
fi

# Clean old logs
find $LOG_DIR -name "odoo.log.*" -mtime +$DAYS_TO_KEEP -delete

echo "Log rotation completed at $(date)"
```

### 4.3. Error Analysis Script

```bash
#!/bin/bash
# /opt/odoo19/scripts/analyze-errors.sh

echo "=== Odoo Error Analysis - $(date) ==="

# Most common errors (last 1000 lines)
echo "1. Top 10 Most Common Errors:"
docker-compose logs --tail=1000 odoo | grep -i error | sort | uniq -c | sort -nr | head -10

# Database connection errors
echo "2. Database Connection Errors:"
docker-compose logs --tail=500 odoo | grep -i "database\|connection\|psycopg"

# Permission errors
echo "3. Permission Errors:"
docker-compose logs --tail=500 odoo | grep -i "permission\|access denied"

# Memory errors
echo "4. Memory Related Errors:"
docker-compose logs --tail=500 odoo | grep -i "memory\|oom"

# Recent errors (last 50 lines)
echo "5. Recent Error Details:"
docker-compose logs --tail=50 odoo | grep -i error -A 2 -B 2

echo "=== Analysis Completed ==="
```

## 5. UPDATE & DEPLOYMENT

### 5.1. Update Code từ Git

```bash
#!/bin/bash
# /opt/odoo19/scripts/update-code.sh

cd /opt/odoo19

echo "Pulling latest code..."
git fetch origin 19.0
git reset --hard origin/19.0

echo "Rebuilding Docker images..."
docker-compose build --no-cache odoo

echo "Restarting services..."
docker-compose down
docker-compose up -d

echo "Running database update..."
docker-compose exec odoo odoo-bin -u all -d odoo19_production --stop-after-init

echo "Update completed at $(date)"
```

### 5.2. Module Installation/Update

```bash
# Install new module
docker-compose exec odoo odoo-bin -i module_name -d odoo19_production --stop-after-init

# Update existing module
docker-compose exec odoo odoo-bin -u module_name -d odoo19_production --stop-after-init

# Update all modules
docker-compose exec odoo odoo-bin -u all -d odoo19_production --stop-after-init
```

## 6. CRON JOBS VẬN HÀNH

```bash
# Cấu hình crontab
sudo crontab -e

# Thêm các jobs sau:

# Backup database hàng ngày lúc 2:00 AM
0 2 * * * /opt/odoo19/scripts/backup-db.sh >> /var/log/odoo19-backup.log 2>&1

# Health check mỗi 15 phút
*/15 * * * * /opt/odoo19/scripts/health-check.sh >> /var/log/odoo19-health.log 2>&1

# Log rotation hàng tuần
0 3 * * 0 /opt/odoo19/scripts/rotate-logs.sh >> /var/log/odoo19-rotation.log 2>&1

# Update code hàng tuần (chỉ nếu cần)
# 0 4 * * 0 /opt/odoo19/scripts/update-code.sh >> /var/log/odoo19-update.log 2>&1
```

## 7. EMERGENCY PROCEDURES

### 7.1. Khắc phục sự cố khẩn cấp

```bash
#!/bin/bash
# /opt/odoo19/scripts/emergency-recovery.sh

echo "=== EMERGENCY RECOVERY STARTED ==="

# Stop all services
echo "Stopping all services..."
docker-compose down

# Check disk space
echo "Checking disk space..."
df -h

# Clean Docker cache if needed
echo "Cleaning Docker cache..."
docker system prune -f

# Start database first
echo "Starting database..."
docker-compose up -d db

# Wait for database
sleep 10

# Start Odoo in safe mode
echo "Starting Odoo..."
docker-compose up -d odoo

# Health check
sleep 30
curl -I http://localhost:8069/web/health

echo "=== EMERGENCY RECOVERY COMPLETED ==="
```

### 7.2. Rollback Procedures

```bash
# Rollback to previous Git version
cd /opt/odoo19
git log --oneline -5  # Xem 5 commits gần nhất
git reset --hard <commit_hash>
docker-compose build --no-cache
docker-compose restart

# Restore from backup
/opt/odoo19/scripts/restore-db.sh /opt/odoo19/backups/odoo_backup_YYYYMMDD_HHMMSS.sql.gz
```

## 8. QUICK REFERENCE COMMANDS

```bash
# Khởi động nhanh
alias odoo-start='cd /opt/odoo19 && docker-compose up -d'

# Dừng nhanh
alias odoo-stop='cd /opt/odoo19 && docker-compose down'

# Restart nhanh
alias odoo-restart='cd /opt/odoo19 && docker-compose restart odoo'

# Xem logs nhanh
alias odoo-logs='cd /opt/odoo19 && docker-compose logs -f odoo'

# Health check nhanh
alias odoo-health='cd /opt/odoo19 && ./scripts/health-check.sh'

# Backup nhanh
alias odoo-backup='cd /opt/odoo19 && ./scripts/backup-db.sh'
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

- **Luôn backup trước khi thực hiện thay đổi**
- **Test trên staging trước khi deploy production**
- **Monitor logs sau mỗi thay đổi**
- **Giữ contact với team development khi có vấn đề**

## 📞 LIÊN HỆ KHẨN CẤP

- **DevOps Team:** +84xxx-xxx-xxx
- **Database Admin:** +84xxx-xxx-xxx  
- **System Admin:** +84xxx-xxx-xxx