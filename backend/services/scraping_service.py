# backend/services/scraping_service.py
import requests
import time
import hashlib
import ssl
import urllib3
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from flask import current_app
from models import db, Website, Page, Snippet
from services.auth_service import AuditService
from services.azure_openai_service import get_azure_openai_service
import concurrent.futures
import threading

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

robots = RobotFileParser()


class ScrapingService:
    """Web scraping orchestration service"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Disable SSL verification for development
        self.session.verify = False
        self.driver = None
        self._lock = threading.Lock()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if self.driver:
            return
        
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki-list')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            current_app.logger.info("Selenium WebDriver initialized")
            
        except Exception as e:
            current_app.logger.warning(f"Failed to initialize Selenium: {e}")
            self.driver = None
    
    def _check_robots_txt(self, url, user_agent='*'):
        """Check if URL is allowed by robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = self.session.get(robots_url, timeout=10, verify=False)
            if response.status_code == 200:
                # Simple robots.txt parsing - can be enhanced
                robots_content = response.text.lower()
                if 'disallow: /' in robots_content and user_agent.lower() in robots_content:
                    return False
            
            return True
            
        except Exception as e:
            current_app.logger.debug(f"Robots.txt check failed for {url}: {e}")
            return True  # Allow by default if check fails
    
    def scrape_single_page(self, website_id, url, use_selenium=False, depth=0):
        """Scrape a single page"""
        try:
            website = Website.query.get(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found',
                    'page': None
                }
            
            # Check robots.txt if enabled
            if website.respect_robots_txt and not self._check_robots_txt(url):
                return {
                    'success': False,
                    'error': 'Blocked by robots.txt',
                    'page': None
                }
            
            # Rate limiting
            if website.rate_limit_delay > 0:
                time.sleep(website.rate_limit_delay)
            
            start_time = time.time()
            
            # Choose scraping method
            if use_selenium or website.auth_type in ['oauth', 'api_key']:
                result = self._scrape_with_selenium(url, website)
            else:
                result = self._scrape_with_requests(url, website)
            
            if not result['success']:
                return result
            
            load_time = time.time() - start_time
            
            # Extract text content
            soup = BeautifulSoup(result['html'], 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            extracted_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Get page title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ''
            
            # Calculate content hash
            content_hash = hashlib.sha256(result['html'].encode('utf-8')).hexdigest()
            
            # Check if page already exists with same content
            existing_page = Page.query.filter_by(
                website_id=website_id, 
                url=url,
                hash_content=content_hash
            ).first()
            
            if existing_page:
                return {
                    'success': True,
                    'message': 'Page content unchanged',
                    'page': existing_page.to_dict()
                }
            
            # Create new page record
            page = Page(
                website_id=website_id,
                url=url,
                title=title[:200] if title else None,
                raw_html=result['html'],
                extracted_text=extracted_text,
                status_code=result.get('status_code', 200),
                content_type=result.get('content_type', 'text/html'),
                content_length=len(result['html']),
                load_time=round(load_time, 3),
                hash_content=content_hash
            )
            
            # Set metadata
            metadata = {
                'scraping_method': 'selenium' if use_selenium else 'requests',
                'depth': depth,
                'scraped_at': datetime.utcnow().isoformat()
            }
            page.set_metadata(metadata)
            
            db.session.add(page)
            db.session.flush()  # Get page ID
            
            # AI analysis if available
            ai_service = get_azure_openai_service()
            if ai_service.is_available() and extracted_text:
                # Summarize content
                summary_result = ai_service.summarize_content(extracted_text)
                if summary_result['success']:
                    page.summary = summary_result['summary']
                
                # Extract entities
                entities_result = ai_service.extract_entities(extracted_text)
                if entities_result['success']:
                    page.set_entities(entities_result['entities'])
                
                # Analyze sentiment
                sentiment_result = ai_service.analyze_sentiment(extracted_text)
                if sentiment_result['success']:
                    page.sentiment_score = sentiment_result['sentiment']['score']
            
            db.session.commit()
            
            # Update website stats
            website.total_pages = Page.query.filter_by(website_id=website_id).count()
            website.last_crawled = datetime.utcnow()
            website.last_error = None
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Page scraped successfully',
                'page': page.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Scrape page error for {url}: {e}")
            
            # Update website error status
            try:
                website = Website.query.get(website_id)
                if website:
                    website.last_error = str(e)
                    db.session.commit()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e),
                'page': None
            }
    
    def _scrape_with_requests(self, url, website):
        """Scrape using requests library with SSL bypass"""
        try:
            # Setup authentication if required
            auth = None
            headers = {}
            
            if website.auth_type == 'basic':
                auth_config = website.get_auth_config()
                auth = (auth_config.get('username', ''), auth_config.get('password', ''))
            elif website.auth_type == 'api_key':
                auth_config = website.get_auth_config()
                headers['Authorization'] = f"Bearer {auth_config.get('api_key', '')}"
            
            # Create SSL context that ignores verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Make request with SSL verification disabled
            response = self.session.get(
                url,
                auth=auth,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'html': response.text,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _scrape_with_selenium(self, url, website):
        """Scrape using Selenium WebDriver"""
        try:
            with self._lock:
                if not self.driver:
                    self._init_selenium()
                
                if not self.driver:
                    return {
                        'success': False,
                        'error': 'Selenium WebDriver not available'
                    }
                
                # Navigate to page
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Handle authentication if needed
                auth_config = website.get_auth_config()
                if website.auth_type == 'basic' and auth_config:
                    # Handle basic auth through URL or form
                    pass  # Implementation depends on specific requirements
                
                # Get page source
                html = self.driver.page_source
                
                return {
                    'success': True,
                    'html': html,
                    'status_code': 200,
                    'content_type': 'text/html'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def crawl_website(self, website_id, user_id, max_pages=None, use_selenium=False):
        """Crawl entire website following links up to specified depth"""
        try:
            website = Website.query.get(website_id)
            if not website:
                return {
                    'success': False,
                    'message': 'Website not found',
                    'stats': None
                }
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='start_crawl',
                resource_type='website',
                resource_id=website_id,
                details={'url': website.url}
            )
            
            crawled_urls = set()
            urls_to_crawl = [(website.url, 0)]  # (url, depth)
            stats = {
                'pages_crawled': 0,
                'pages_failed': 0,
                'start_time': datetime.utcnow(),
                'errors': []
            }
            
            while urls_to_crawl and (not max_pages or stats['pages_crawled'] < max_pages):
                current_url, depth = urls_to_crawl.pop(0)
                
                if current_url in crawled_urls:
                    continue
                
                if depth > website.crawl_depth:
                    continue
                
                crawled_urls.add(current_url)
                
                # Scrape current page
                result = self.scrape_single_page(website_id, current_url, use_selenium, depth)
                
                if result['success']:
                    stats['pages_crawled'] += 1
                    
                    # Find links to follow if not at max depth
                    if depth < website.crawl_depth:
                        new_urls = self._extract_links(
                            result['page'].get('raw_html', ''),
                            current_url,
                            website.follow_external_links
                        )
                        
                        for new_url in new_urls:
                            if new_url not in crawled_urls:
                                urls_to_crawl.append((new_url, depth + 1))
                else:
                    stats['pages_failed'] += 1
                    stats['errors'].append({
                        'url': current_url,
                        'error': result['error']
                    })
                
                # Rate limiting between pages
                if website.rate_limit_delay > 0:
                    time.sleep(website.rate_limit_delay)
            
            stats['end_time'] = datetime.utcnow()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            # Log completion
            AuditService.log_action(
                user_id=user_id,
                action='complete_crawl',
                resource_type='website',
                resource_id=website_id,
                details=stats
            )
            
            return {
                'success': True,
                'message': f"Crawl completed. {stats['pages_crawled']} pages crawled.",
                'stats': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"Crawl website error: {e}")
            return {
                'success': False,
                'message': 'Crawl failed',
                'stats': None
            }
    
    def _extract_links(self, html, base_url, follow_external=False):
        """Extract links from HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            base_domain = urlparse(base_url).netloc
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                parsed_url = urlparse(absolute_url)
                
                # Skip invalid URLs
                if not parsed_url.scheme or not parsed_url.netloc:
                    continue
                
                # Skip non-HTTP protocols
                if parsed_url.scheme not in ['http', 'https']:
                    continue
                
                # Check external links policy
                if not follow_external and parsed_url.netloc != base_domain:
                    continue
                
                # Skip common file extensions that aren't web pages
                if parsed_url.path.lower().endswith(('.pdf', '.jpg', '.png', '.gif', '.zip', '.exe')):
                    continue
                
                links.append(absolute_url)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            current_app.logger.debug(f"Link extraction error: {e}")
            return []
    
    def schedule_crawl(self, website_id, user_id, schedule_type='once', schedule_config=None):
        """Schedule a crawl job"""
        try:
            from models import ScheduledJob
            
            website = Website.query.get(website_id)
            if not website:
                return {
                    'success': False,
                    'message': 'Website not found'
                }
            
            # Calculate next run time
            next_run = self._calculate_next_run(schedule_type, schedule_config)
            
            # Create scheduled job
            job = ScheduledJob(
                website_id=website_id,
                name=f"Crawl {website.name or website.url}",
                schedule_type=schedule_type,
                is_active=True,
                next_run=next_run
            )
            
            if schedule_config:
                job.set_schedule_config(schedule_config)
            
            db.session.add(job)
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='schedule_crawl',
                resource_type='website',
                resource_id=website_id,
                details={
                    'schedule_type': schedule_type,
                    'next_run': next_run.isoformat() if next_run else None
                }
            )
            
            return {
                'success': True,
                'message': 'Crawl scheduled successfully',
                'job': job.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Schedule crawl error: {e}")
            return {
                'success': False,
                'message': 'Failed to schedule crawl'
            }
    
    def _calculate_next_run(self, schedule_type, schedule_config=None):
        """Calculate next run time based on schedule type"""
        now = datetime.utcnow()
        
        if schedule_type == 'once':
            return now + timedelta(minutes=1)
        elif schedule_type == 'hourly':
            return now + timedelta(hours=1)
        elif schedule_type == 'daily':
            return now + timedelta(days=1)
        elif schedule_type == 'weekly':
            return now + timedelta(weeks=1)
        elif schedule_type == 'monthly':
            return now + timedelta(days=30)
        else:
            return now + timedelta(hours=24)
    
    def get_crawl_status(self, website_id):
        """Get current crawl status for website"""
        try:
            website = Website.query.get(website_id)
            if not website:
                return {
                    'success': False,
                    'message': 'Website not found',
                    'status': None
                }
            
            # Get recent pages count
            recent_pages = Page.query.filter(
                Page.website_id == website_id,
                Page.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            status = {
                'website_id': website_id,
                'status': website.status,
                'last_crawled': website.last_crawled.isoformat() if website.last_crawled else None,
                'last_error': website.last_error,
                'total_pages': website.total_pages,
                'recent_pages_24h': recent_pages
            }
            
            return {
                'success': True,
                'status': status
            }
            
        except Exception as e:
            current_app.logger.error(f"Get crawl status error: {e}")
            return {
                'success': False,
                'message': 'Failed to get crawl status',
                'status': None
            }
    
    def stop_crawl(self, website_id, user_id):
        """Stop ongoing crawl for website"""
        try:
            website = Website.query.get(website_id)
            if not website:
                return {
                    'success': False,
                    'message': 'Website not found'
                }
            
            # Update website status
            website.status = 'paused'
            db.session.commit()
            
            # Log audit event
            AuditService.log_action(
                user_id=user_id,
                action='stop_crawl',
                resource_type='website',
                resource_id=website_id
            )
            
            return {
                'success': True,
                'message': 'Crawl stopped successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Stop crawl error: {e}")
            return {
                'success': False,
                'message': 'Failed to stop crawl'
            }
    
    def __del__(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass