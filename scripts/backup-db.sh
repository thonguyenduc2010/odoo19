
DB_NAME="erp"
BACKUP_DIR="/data/odoo/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup with compression
docker-compose exec db pg_dump -U odoo -h localhost $DB_NAME | gzip > $BACKUP_DIR/erp_backup_$DATE.sql.gz

# Keep only last 7 days backups
find $BACKUP_DIR -name "erp_backup_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: erp_backup_$DATE.sql.gz"