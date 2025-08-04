import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import Dict, List, Optional
import os

class WebResearch:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def detect_search_intent(self, query: str) -> Dict[str, any]:
        """Kullanıcı sorgusunun ne tür bir araştırma gerektirdiğini tespit eder"""
        query_lower = query.lower()
        
        # Hava durumu tespiti
        weather_keywords = ['hava', 'hava durumu', 'sıcaklık', 'yağmur', 'güneş', 'rüzgar', 'nem', 'derece']
        if any(keyword in query_lower for keyword in weather_keywords):
            # Şehir adını çıkar
            city = self.extract_city_from_query(query)
            return {
                'type': 'weather',
                'city': city,
                'confidence': 0.9
            }
        
        # Ulaşım bilgisi tespiti
        transport_keywords = ['vapur', 'otobüs', 'metro', 'tren', 'uçak', 'feribot', 'saat', 'sefer']
        if any(keyword in query_lower for keyword in transport_keywords):
            return {
                'type': 'transport',
                'confidence': 0.9
            }
        
        # Yol tarifi tespiti
        route_keywords = ['yol', 'tarif', 'nasıl giderim', 'adres', 'konum', 'harita', 'gps']
        if any(keyword in query_lower for keyword in route_keywords):
            return {
                'type': 'route',
                'confidence': 0.8
            }
        
        # Haber tespiti
        news_keywords = ['haber', 'güncel', 'son dakika', 'olay', 'gelişme']
        if any(keyword in query_lower for keyword in news_keywords):
            return {
                'type': 'news',
                'confidence': 0.7
            }
        
        # Fiyat karşılaştırma
        price_keywords = ['fiyat', 'kaç para', 'ne kadar', 'ucuz', 'pahalı']
        if any(keyword in query_lower for keyword in price_keywords):
            return {
                'type': 'price',
                'confidence': 0.6
            }
        
        # Genel arama
        return {
            'type': 'general_search',
            'confidence': 0.5
        }
    
    def extract_city_from_query(self, query: str) -> str:
        """Sorgudan şehir adını çıkarır"""
        # Türkiye şehirleri
        turkish_cities = [
            'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 'konya', 'şanlıurfa',
            'gaziantep', 'kocaeli', 'mersin', 'diyarbakır', 'hatay', 'manisa', 'kayseri',
            'samsun', 'balıkesir', 'kahramanmaraş', 'van', 'aydın', 'tekirdağ', 'sakarya',
            'denizli', 'muğla', 'eskişehir', 'malatya', 'erzurum', 'afyonkarahisar', 'trabzon',
            'ordu', 'çorum', 'giresun', 'elazığ', 'tokat', 'çanakkale', 'osmaniye', 'kırıkkale',
            'antalya', 'nevşehir', 'kırşehir', 'niğde', 'aksaray', 'karaman', 'kırklareli',
            'edirne', 'tekirdağ', 'çanakkale', 'balıkesir', 'izmir', 'aydın', 'muğla', 'antalya'
        ]
        
        query_lower = query.lower()
        for city in turkish_cities:
            if city in query_lower:
                return city.title()
        
        # Eğer şehir bulunamazsa, varsayılan olarak İstanbul
        return "İstanbul"
    
    def get_weather(self, city: str) -> Dict[str, any]:
        """Hava durumu bilgisi alır"""
        try:
            # OpenWeatherMap API kullanımı (ücretsiz)
            api_key = os.getenv('OPENWEATHER_API_KEY', '')
            if api_key:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city},TR&appid={api_key}&units=metric&lang=tr"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'success': True,
                        'city': city,
                        'temperature': data['main']['temp'],
                        'feels_like': data['main']['feels_like'],
                        'humidity': data['main']['humidity'],
                        'description': data['weather'][0]['description'],
                        'wind_speed': data['wind']['speed'],
                        'pressure': data['main']['pressure'],
                        'timestamp': datetime.now().strftime("%H:%M")
                    }
            
            # Alternatif: Web scraping ile hava durumu
            return self.scrape_weather(city)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"{city} için hava durumu bilgisi alınamadı."
            }
    
    def scrape_weather(self, city: str) -> Dict[str, any]:
        """Web scraping ile hava durumu bilgisi alır"""
        try:
            # Google hava durumu sayfasını ara
            search_query = f"{city} hava durumu"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hava durumu bilgilerini çıkar
            weather_info = {
                'success': True,
                'city': city,
                'source': 'Google',
                'timestamp': datetime.now().strftime("%H:%M")
            }
            
            # Sıcaklık bilgisi
            temp_elements = soup.find_all('span', {'class': 'wob_t'})
            if temp_elements:
                weather_info['temperature'] = temp_elements[0].text
            
            # Hava durumu açıklaması
            desc_elements = soup.find_all('span', {'class': 'wob_dc'})
            if desc_elements:
                weather_info['description'] = desc_elements[0].text
            
            return weather_info
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"{city} için hava durumu bilgisi alınamadı."
            }
    
    def get_route_info(self, origin: str, destination: str) -> Dict[str, any]:
        """Yol tarifi bilgisi alır"""
        try:
            # Google Maps API kullanımı (ücretsiz sürüm)
            api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
            if api_key:
                url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={api_key}&language=tr"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'OK':
                        route = data['routes'][0]['legs'][0]
                        return {
                            'success': True,
                            'origin': route['start_address'],
                            'destination': route['end_address'],
                            'distance': route['distance']['text'],
                            'duration': route['duration']['text'],
                            'steps': [step['html_instructions'] for step in route['steps']],
                            'timestamp': datetime.now().strftime("%H:%M")
                        }
            
            # Alternatif: Web scraping ile yol tarifi
            return self.scrape_route_info(origin, destination)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Yol tarifi bilgisi alınamadı."
            }
    
    def scrape_route_info(self, origin: str, destination: str) -> Dict[str, any]:
        """Web scraping ile yol tarifi bilgisi alır"""
        try:
            search_query = f"{origin} {destination} yol tarifi"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'success': True,
                'origin': origin,
                'destination': destination,
                'source': 'Google',
                'message': f"{origin} ile {destination} arasındaki yol tarifi için Google Maps'i kullanabilirsiniz.",
                'timestamp': datetime.now().strftime("%H:%M")
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Yol tarifi bilgisi alınamadı."
            }
    
    def search_news(self, query: str) -> Dict[str, any]:
        """Güncel haberler arar"""
        try:
            search_query = f"{query} haber güncel"
            search_url = f"https://www.google.com/search?q={search_query}&tbm=nws"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            news_elements = soup.find_all('div', {'class': 'g'})
            
            for element in news_elements[:5]:  # İlk 5 haberi al
                title_element = element.find('h3')
                link_element = element.find('a')
                snippet_element = element.find('div', {'class': 'VwiC3b'})
                
                if title_element and link_element:
                    news_items.append({
                        'title': title_element.text,
                        'url': link_element['href'],
                        'snippet': snippet_element.text if snippet_element else ''
                    })
            
            return {
                'success': True,
                'query': query,
                'news': news_items,
                'count': len(news_items),
                'timestamp': datetime.now().strftime("%H:%M")
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Haber arama yapılamadı."
            }
    
    def get_transport_info(self, query: str) -> Dict[str, any]:
        """Ulaşım bilgisi alır (vapur, otobüs, metro, tren saatleri vb.)"""
        try:
            # Google'da ulaşım bilgisi ara
            search_query = f"{query} saat sefer bilgi"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ulaşım bilgilerini çıkar
            transport_info = {
                'success': True,
                'query': query,
                'source': 'Google',
                'timestamp': datetime.now().strftime("%H:%M"),
                'info': []
            }
            
            # Arama sonuçlarından bilgi çıkar
            result_elements = soup.find_all('div', {'class': 'g'})
            
            for element in result_elements[:5]:  # İlk 5 sonucu al
                title_element = element.find('h3')
                snippet_element = element.find('div', {'class': 'VwiC3b'})
                
                if title_element and snippet_element:
                    transport_info['info'].append({
                        'title': title_element.text,
                        'snippet': snippet_element.text
                    })
            
            # Eğer yeterli bilgi yoksa, genel arama yap
            if len(transport_info['info']) < 2:
                general_result = self.search_general(query)
                if general_result['success']:
                    transport_info['info'].extend(general_result['results'])
            
            return transport_info
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"{query} için ulaşım bilgisi alınamadı."
            }
    
    def search_general(self, query: str) -> Dict[str, any]:
        """Genel web araması yapar"""
        try:
            search_url = f"https://www.google.com/search?q={query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            result_elements = soup.find_all('div', {'class': 'g'})
            
            for element in result_elements[:3]:  # İlk 3 sonucu al
                title_element = element.find('h3')
                link_element = element.find('a')
                snippet_element = element.find('div', {'class': 'VwiC3b'})
                
                if title_element and link_element:
                    results.append({
                        'title': title_element.text,
                        'url': link_element['href'],
                        'snippet': snippet_element.text if snippet_element else ''
                    })
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'count': len(results),
                'timestamp': datetime.now().strftime("%H:%M")
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Arama yapılamadı."
            }
    
    def research_query(self, query: str) -> Dict[str, any]:
        """Ana araştırma fonksiyonu"""
        intent = self.detect_search_intent(query)
        
        if intent['type'] == 'weather':
            return self.get_weather(intent.get('city', 'İstanbul'))
        elif intent['type'] == 'transport':
            return self.get_transport_info(query)
        elif intent['type'] == 'route':
            # Yol tarifi için origin ve destination çıkar
            locations = self.extract_locations_from_query(query)
            if len(locations) >= 2:
                return self.get_route_info(locations[0], locations[1])
            else:
                return {
                    'success': False,
                    'message': "Yol tarifi için başlangıç ve bitiş noktalarını belirtin."
                }
        elif intent['type'] == 'news':
            return self.search_news(query)
        else:
            return self.search_general(query)
    
    def extract_locations_from_query(self, query: str) -> List[str]:
        """Sorgudan konum bilgilerini çıkarır"""
        # Basit konum çıkarma - gerçek uygulamada daha gelişmiş NLP kullanılabilir
        locations = []
        query_lower = query.lower()
        
        # Türkiye şehirleri
        turkish_cities = [
            'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 'konya', 'şanlıurfa',
            'gaziantep', 'kocaeli', 'mersin', 'diyarbakır', 'hatay', 'manisa', 'kayseri'
        ]
        
        for city in turkish_cities:
            if city in query_lower:
                locations.append(city.title())
        
        return locations[:2]  # En fazla 2 konum döndür 