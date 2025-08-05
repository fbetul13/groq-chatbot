#!/bin/bash

# ========================================
# AI Chatbot Docker Setup Script
# ========================================

set -e  # Exit on any error

echo "🚀 AI Chatbot Docker Kurulum Scripti"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Docker kontrol ediliyor..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker yüklü değil! Lütfen Docker'ı yükleyin: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose yüklü değil! Lütfen Docker Compose'u yükleyin."
        exit 1
    fi
    
    print_success "Docker ve Docker Compose yüklü"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env dosyası bulunamadı. Oluşturuluyor..."
        cp env_example.txt .env
        print_success ".env dosyası oluşturuldu"
        print_warning "Lütfen .env dosyasını düzenleyerek API anahtarlarınızı ekleyin!"
        echo ""
        echo "Önemli: .env dosyasında şu değerleri güncelleyin:"
        echo "  - GROQ_API_KEY: https://console.groq.com/keys adresinden alın"
        echo "  - SECRET_KEY: Güvenli bir secret key oluşturun"
        echo ""
        read -p "Devam etmek için Enter'a basın..."
    else
        print_success ".env dosyası mevcut"
    fi
}

# Generate secret key
generate_secret_key() {
    print_status "Secret key oluşturuluyor..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    print_success "Secret key oluşturuldu ve .env dosyasına eklendi"
}

# Build Docker images
build_images() {
    print_status "Docker imajları oluşturuluyor..."
    docker-compose build --no-cache
    print_success "Docker imajları oluşturuldu"
}

# Start services
start_services() {
    print_status "Servisler başlatılıyor..."
    docker-compose up -d
    print_success "Servisler başlatıldı"
}

# Check service health
check_health() {
    print_status "Servis sağlığı kontrol ediliyor..."
    
    # Wait for services to start
    sleep 10
    
    # Check backend health
    if curl -f http://localhost:5002/api/health &> /dev/null; then
        print_success "Backend servisi çalışıyor"
    else
        print_warning "Backend servisi henüz hazır değil"
    fi
    
    # Check frontend health
    if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
        print_success "Frontend servisi çalışıyor"
    else
        print_warning "Frontend servisi henüz hazır değil"
    fi
}

# Show service information
show_info() {
    echo ""
    echo "🎉 Kapsamlı Docker Kurulumu Tamamlandı!"
    echo "========================================"
    echo ""
    echo "📱 Uygulama URL'leri:"
    echo "  - Frontend: http://localhost:8501"
    echo "  - Backend API: http://localhost:5002"
    echo "  - Nginx Proxy: http://localhost:80"
    echo "  - Grafana Dashboard: http://localhost:3000"
    echo "  - Prometheus Metrics: http://localhost:9090"
    echo ""
    echo "🗄️  Veritabanı Servisleri:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis Cache: localhost:6379"
    echo ""
    echo "🔧 Yönetim Komutları:"
    echo "  - Tüm servisleri durdur: docker-compose down"
    echo "  - Logları görüntüle: docker-compose logs -f"
    echo "  - Servisleri yeniden başlat: docker-compose restart"
    echo "  - Servisleri güncelle: docker-compose pull && docker-compose up -d"
    echo "  - Sadece belirli servisi yeniden başlat: docker-compose restart [service-name]"
    echo ""
    echo "📁 Veri Konumları:"
    echo "  - PostgreSQL: Docker volume (postgres_data)"
    echo "  - Redis: Docker volume (redis_data)"
    echo "  - Backend: Docker volume (backend_data, backend_logs, backend_uploads)"
    echo "  - Frontend: Docker volume (frontend_data)"
    echo "  - Nginx: Docker volume (nginx_logs)"
    echo "  - Monitoring: Docker volume (prometheus_data, grafana_data)"
    echo ""
    echo "⚠️  Önemli Notlar:"
    echo "  - İlk kullanımda admin hesabı oluşturun"
    echo "  - .env dosyasındaki API anahtarlarını kontrol edin"
    echo "  - Güvenlik için varsayılan şifreleri değiştirin"
    echo "  - Grafana giriş: admin / admin123"
    echo "  - PostgreSQL: chatbot_user / chatbot_pass"
    echo "  - Redis: redis_pass"
    echo ""
    echo "🚀 Sistem Durumu:"
    echo "  - Tüm servisler otomatik olarak başlatılır"
    echo "  - Health check'ler ile servis durumu izlenir"
    echo "  - Rate limiting ve güvenlik önlemleri aktif"
    echo "  - Monitoring ve loglama sistemi hazır"
    echo ""
}

# Main setup function
main() {
    echo "Docker kurulumu başlatılıyor..."
    echo ""
    
    check_docker
    check_env_file
    generate_secret_key
    build_images
    start_services
    check_health
    show_info
}

# Run main function
main "$@" 