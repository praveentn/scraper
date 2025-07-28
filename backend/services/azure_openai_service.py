# backend/services/azure_openai_service.py
import os
import json
import re
from datetime import datetime
from flask import current_app
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional


class AzureOpenAIService:
    """Azure OpenAI integration service for content analysis and extraction"""
    
    def __init__(self):
        self.client = None
        self.config = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            self.config = {
                'endpoint': current_app.config.get('AZURE_OPENAI_ENDPOINT'),
                'api_key': current_app.config.get('AZURE_OPENAI_API_KEY'),
                'api_version': current_app.config.get('AZURE_OPENAI_API_VERSION'),
                'deployment': current_app.config.get('AZURE_OPENAI_DEPLOYMENT'),
                'model': current_app.config.get('AZURE_OPENAI_MODEL'),
                'max_tokens': current_app.config.get('AZURE_OPENAI_MAX_TOKENS', 4000),
                'temperature': current_app.config.get('AZURE_OPENAI_TEMPERATURE', 0.7)
            }
            
            # Validate configuration
            if not self.config['api_key'] or self.config['api_key'] == 'openai-key-placeholder':
                current_app.logger.warning("Azure OpenAI API key not configured")
                return
            
            if not self.config['endpoint']:
                current_app.logger.warning("Azure OpenAI endpoint not configured")
                return
            
            # Initialize client
            self.client = AzureOpenAI(
                api_version=self.config['api_version'],
                azure_endpoint=self.config['endpoint'],
                api_key=self.config['api_key']
            )
            
            current_app.logger.info("Azure OpenAI client initialized successfully")
            
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None
    
    def _make_request(self, messages: List[Dict], max_tokens: int = None, temperature: float = None):
        """Make request to Azure OpenAI API"""
        if not self.client:
            return {
                'success': False,
                'error': 'Azure OpenAI client not initialized',
                'content': None
            }
        
        try:
            response = self.client.chat.completions.create(
                model=self.config['deployment'],
                messages=messages,
                max_completion_tokens=max_tokens or self.config['max_tokens'],
                temperature=temperature or self.config['temperature'],
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            content = response.choices[0].message.content
            
            return {
                'success': True,
                'error': None,
                'content': content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Azure OpenAI API request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def summarize_content(self, content: str, max_length: int = 200) -> Dict[str, Any]:
        """Summarize web page content"""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'No content to summarize',
                'summary': None
            }
        
        # Truncate content if too long
        if len(content) > 8000:
            content = content[:8000] + "..."
        
        messages = [
            {
                "role": "system",
                "content": f"You are a content summarization expert. Summarize the following web page content in {max_length} characters or less. Focus on key information, main topics, and important details. Be concise and informative."
            },
            {
                "role": "user",
                "content": f"Please summarize this content:\n\n{content}"
            }
        ]
        
        result = self._make_request(messages, max_tokens=300, temperature=0.3)
        
        if result['success']:
            summary = result['content'].strip()
            # Ensure summary doesn't exceed max_length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return {
                'success': True,
                'error': None,
                'summary': summary,
                'usage': result.get('usage')
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'summary': None
            }
    
    def extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract named entities from content"""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'No content to analyze',
                'entities': []
            }
        
        # Truncate content if too long
        if len(content) > 6000:
            content = content[:6000] + "..."
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert in named entity recognition. Extract people, organizations, locations, dates, and other important entities from the text. Return the results as a JSON array where each entity has 'text', 'type', and 'confidence' fields. Types should be: PERSON, ORGANIZATION, LOCATION, DATE, MONEY, PRODUCT, EVENT, or OTHER."
            },
            {
                "role": "user",
                "content": f"Extract entities from this text:\n\n{content}"
            }
        ]
        
        result = self._make_request(messages, max_tokens=1000, temperature=0.1)
        
        if result['success']:
            try:
                # Try to parse JSON response
                entities_text = result['content'].strip()
                
                # Clean up response if it contains extra text
                json_match = re.search(r'\[.*\]', entities_text, re.DOTALL)
                if json_match:
                    entities_text = json_match.group()
                
                entities = json.loads(entities_text)
                
                # Validate entity structure
                validated_entities = []
                for entity in entities:
                    if isinstance(entity, dict) and 'text' in entity and 'type' in entity:
                        validated_entities.append({
                            'text': entity.get('text', ''),
                            'type': entity.get('type', 'OTHER'),
                            'confidence': float(entity.get('confidence', 0.8))
                        })
                
                return {
                    'success': True,
                    'error': None,
                    'entities': validated_entities,
                    'usage': result.get('usage')
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.warning(f"Failed to parse entities JSON: {e}")
                return {
                    'success': False,
                    'error': 'Failed to parse entity extraction results',
                    'entities': []
                }
        else:
            return {
                'success': False,
                'error': result['error'],
                'entities': []
            }
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content"""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'No content to analyze',
                'sentiment': None
            }
        
        # Truncate content if too long
        if len(content) > 4000:
            content = content[:4000] + "..."
        
        messages = [
            {
                "role": "system",
                "content": "You are a sentiment analysis expert. Analyze the sentiment of the given text and return a score between -1.0 (very negative) and 1.0 (very positive), where 0.0 is neutral. Also provide a brief explanation. Respond in JSON format with 'score' (number) and 'explanation' (string) fields."
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of this text:\n\n{content}"
            }
        ]
        
        result = self._make_request(messages, max_tokens=200, temperature=0.1)
        
        if result['success']:
            try:
                # Try to parse JSON response
                sentiment_text = result['content'].strip()
                
                # Clean up response if it contains extra text
                json_match = re.search(r'\{.*\}', sentiment_text, re.DOTALL)
                if json_match:
                    sentiment_text = json_match.group()
                
                sentiment_data = json.loads(sentiment_text)
                
                score = float(sentiment_data.get('score', 0.0))
                explanation = sentiment_data.get('explanation', '')
                
                # Ensure score is in valid range
                score = max(-1.0, min(1.0, score))
                
                return {
                    'success': True,
                    'error': None,
                    'sentiment': {
                        'score': round(score, 3),
                        'explanation': explanation,
                        'label': 'positive' if score > 0.1 else 'negative' if score < -0.1 else 'neutral'
                    },
                    'usage': result.get('usage')
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.warning(f"Failed to parse sentiment JSON: {e}")
                # Fallback to basic sentiment
                return {
                    'success': True,
                    'error': None,
                    'sentiment': {
                        'score': 0.0,
                        'explanation': 'Unable to determine sentiment',
                        'label': 'neutral'
                    },
                    'usage': result.get('usage')
                }
        else:
            return {
                'success': False,
                'error': result['error'],
                'sentiment': None
            }
    
    def suggest_extraction_rules(self, html_content: str, sample_data: str) -> Dict[str, Any]:
        """Suggest CSS/XPath extraction rules based on HTML content and desired data"""
        if not html_content or not sample_data:
            return {
                'success': False,
                'error': 'Missing HTML content or sample data',
                'rules': []
            }
        
        # Truncate HTML if too long
        if len(html_content) > 6000:
            html_content = html_content[:6000] + "..."
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert web scraper. Given HTML content and a description of the data to extract, suggest CSS selectors or XPath expressions. Return a JSON array where each rule has 'name', 'selector', 'type' (css or xpath), 'attribute' (text, href, src, etc.), and 'description' fields."
            },
            {
                "role": "user",
                "content": f"HTML Content:\n{html_content}\n\nData to extract: {sample_data}\n\nPlease suggest extraction rules:"
            }
        ]
        
        result = self._make_request(messages, max_tokens=1000, temperature=0.2)
        
        if result['success']:
            try:
                # Try to parse JSON response
                rules_text = result['content'].strip()
                
                # Clean up response if it contains extra text
                json_match = re.search(r'\[.*\]', rules_text, re.DOTALL)
                if json_match:
                    rules_text = json_match.group()
                
                rules = json.loads(rules_text)
                
                # Validate rule structure
                validated_rules = []
                for rule in rules:
                    if isinstance(rule, dict) and 'selector' in rule:
                        validated_rules.append({
                            'name': rule.get('name', 'Unnamed Rule'),
                            'selector': rule.get('selector', ''),
                            'type': rule.get('type', 'css'),
                            'attribute': rule.get('attribute', 'text'),
                            'description': rule.get('description', '')
                        })
                
                return {
                    'success': True,
                    'error': None,
                    'rules': validated_rules,
                    'usage': result.get('usage')
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                current_app.logger.warning(f"Failed to parse rules JSON: {e}")
                return {
                    'success': False,
                    'error': 'Failed to parse extraction rule suggestions',
                    'rules': []
                }
        else:
            return {
                'success': False,
                'error': result['error'],
                'rules': []
            }
    
    def analyze_content_changes(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze changes between two versions of content"""
        if not old_content or not new_content:
            return {
                'success': False,
                'error': 'Missing content for comparison',
                'analysis': None
            }
        
        # Truncate content if too long
        if len(old_content) > 3000:
            old_content = old_content[:3000] + "..."
        if len(new_content) > 3000:
            new_content = new_content[:3000] + "..."
        
        messages = [
            {
                "role": "system",
                "content": "You are a content analysis expert. Compare two versions of content and identify key changes, additions, and removals. Provide a concise summary of the differences and their significance."
            },
            {
                "role": "user",
                "content": f"Old Content:\n{old_content}\n\nNew Content:\n{new_content}\n\nPlease analyze the changes:"
            }
        ]
        
        result = self._make_request(messages, max_tokens=500, temperature=0.3)
        
        if result['success']:
            return {
                'success': True,
                'error': None,
                'analysis': result['content'].strip(),
                'usage': result.get('usage')
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'analysis': None
            }
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI service is available"""
        return self.client is not None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration"""
        return {
            'available': self.is_available(),
            'endpoint_configured': bool(self.config and self.config.get('endpoint')),
            'api_key_configured': bool(self.config and self.config.get('api_key') and 
                                     self.config['api_key'] != 'openai-key-placeholder'),
            'model': self.config.get('model') if self.config else None,
            'deployment': self.config.get('deployment') if self.config else None
        }


# Singleton instance
_azure_openai_service = None

def get_azure_openai_service() -> AzureOpenAIService:
    """Get singleton instance of Azure OpenAI service"""
    global _azure_openai_service
    if _azure_openai_service is None:
        _azure_openai_service = AzureOpenAIService()
    return _azure_openai_service