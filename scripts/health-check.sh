echo "=== Odoo 19 Health Check - $(date) ==="

# Check Docker containers
echo "1. Docker Containers:"
docker-compose ps

# Check HTTP response
echo "2. HTTP Response:"
curl -I http://localhost:19000/web/health 2>/dev/null | head -1

# Check database connection
#echo "3. Database Connection:"
#docker-compose exec db pg_isready -h localhost -p 5432

# Check disk space
echo "4. Disk Usage:"
df -h /data/odoo

# Check memory usage
echo "5. Memory Usage:"
free -h

# Check logs for errors (last 10 lines)
echo "6. Recent Errors:"
docker-compose logs odoo --tail=10 | grep -i error

echo "=== Health Check Completed ==="