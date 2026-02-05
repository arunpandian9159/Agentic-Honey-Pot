"""
Technical Analyzer for Advanced Scam Detection.
Analyzes technical indicators including URLs, domains, link shorteners,
suspicious TLDs, and typosquatting detection.
"""

import re
from urllib.parse import urlparse
from typing import Dict, List


class TechnicalAnalyzer:
    """Analyze technical indicators (URLs, domains, etc.) for scam detection."""
    
    def __init__(self):
        # Known link shorteners
        self.link_shorteners = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
            'buff.ly', 'is.gd', 'tiny.cc', 'cli.gs', 'short.link',
            'cutt.ly', 'rebrand.ly', 'shorturl.at'
        ]
        
        # Suspicious TLDs
        self.suspicious_tlds = [
            '.tk', '.ml', '.ga', '.cf', '.gq',  # Free domains
            '.xyz', '.top', '.work', '.click', '.online',  # Commonly used in scams
            '.win', '.loan', '.info'
        ]
        
        # Legitimate bank/service domains (India-specific)
        self.legitimate_domains = [
            'sbi.co.in', 'hdfcbank.com', 'icicibank.com', 'axisbank.com',
            'kotak.com', 'yesbank.in', 'paytm.com', 'phonepe.com',
            'googlepay.com', 'amazon.in', 'flipkart.com', 'government.in',
            'gov.in', 'nic.in', 'incometax.gov.in'
        ]
        
        # Typosquatting patterns for Indian services
        self.typosquat_brands = {
            'paytm': ['paytm', 'pytm', 'paytym', 'paytem', 'paytam', 'paytim'],
            'phonepe': ['phonepe', 'phonpe', 'fonpe', 'phoneepy', 'phonepay'],
            'sbi': ['sbi', 'sbionline', 'onlinesbi', 'sbionlne', 'sbibank'],
            'hdfc': ['hdfc', 'hdfcbank', 'hdfbank', 'hdcf', 'hdfcbnk'],
            'icici': ['icici', 'icicbank', 'icicibnk', 'icicci'],
            'amazon': ['amazon', 'amazn', 'amzon', 'amazoon', 'amazonin'],
        }
        
        # Suspicious URL keywords
        self.suspicious_url_keywords = [
            'verify', 'secure', 'account', 'login', 'update', 
            'confirm', 'validate', 'urgent', 'alert'
        ]
    
    def analyze(self, message: str) -> Dict[str, float]:
        """
        Analyze technical indicators in message.
        
        Returns:
            {
                "url_score": 0.0-1.0,
                "domain_score": 0.0-1.0,
                "urls_found": [list of URLs],
                "overall_technical_score": 0.0-1.0
            }
        """
        # Extract URLs
        urls = self._extract_urls(message)
        
        if not urls:
            return {
                "url_score": 0.0,
                "domain_score": 0.0,
                "urls_found": [],
                "overall_technical_score": 0.0
            }
        
        # Analyze each URL
        url_scores = [self._analyze_url(url) for url in urls]
        avg_url_score = sum(url_scores) / len(url_scores) if url_scores else 0.0
        
        # Analyze domains
        domain_scores = [self._analyze_domain(url) for url in urls]
        avg_domain_score = sum(domain_scores) / len(domain_scores) if domain_scores else 0.0
        
        overall = (avg_url_score * 0.5 + avg_domain_score * 0.5)
        
        return {
            "url_score": avg_url_score,
            "domain_score": avg_domain_score,
            "urls_found": urls,
            "overall_technical_score": overall
        }
    
    def _extract_urls(self, message: str) -> List[str]:
        """Extract all URLs from message."""
        # URL pattern
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        urls = re.findall(url_pattern, message)
        return urls
    
    def _analyze_url(self, url: str) -> float:
        """Analyze URL structure for suspicious patterns."""
        score = 0.0
        
        # Check for IP address instead of domain
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            score += 0.5  # Using IP = very suspicious
        
        # Check for @ symbol (phishing technique)
        if '@' in url:
            score += 0.4
        
        # Check for double slashes after protocol
        if url.count('//') > 1:
            score += 0.3
        
        # Check URL length (very long URLs are suspicious)
        if len(url) > 100:
            score += 0.2
        
        try:
            # Check for too many subdomains
            parsed = urlparse(url)
            if parsed.netloc:
                subdomain_count = parsed.netloc.count('.')
                if subdomain_count > 3:
                    score += 0.3
        except Exception:
            score += 0.2  # Malformed URL
        
        # Check for suspicious keywords in URL
        url_lower = url.lower()
        matches = sum(1 for kw in self.suspicious_url_keywords if kw in url_lower)
        if matches >= 2:
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_domain(self, url: str) -> float:
        """Analyze domain reputation."""
        score = 0.0
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if link shortener
            if any(shortener in domain for shortener in self.link_shorteners):
                score += 0.6  # Link shorteners hide real destination
            
            # Check if suspicious TLD
            if any(domain.endswith(tld) for tld in self.suspicious_tlds):
                score += 0.7
            
            # Check for typosquatting (misspelled legitimate domains)
            score += self._check_typosquatting(domain)
            
            # Check if legitimate domain
            if any(legit in domain for legit in self.legitimate_domains):
                score -= 0.5  # Reduce suspicion for known good domains
                score = max(score, 0.0)  # Don't go negative
            
        except Exception:
            score = 0.5  # Malformed URL = somewhat suspicious
        
        return min(score, 1.0)
    
    def _check_typosquatting(self, domain: str) -> float:
        """Check if domain is typosquatting a known brand."""
        domain_parts = domain.split('.')
        if not domain_parts:
            return 0.0
            
        domain_name = domain_parts[0]
        
        for brand, variants in self.typosquat_brands.items():
            # If domain contains brand-like string but isn't exact match
            if brand in domain_name:
                # Check if it's a legitimate variant
                if domain_name not in variants:
                    # Suspicious: contains brand but not exact
                    return 0.8
            
            # Check for similar strings (basic Levenshtein-like check)
            if self._is_similar(domain_name, brand) and domain_name != brand:
                return 0.6
        
        return 0.0
    
    def _is_similar(self, str1: str, str2: str) -> bool:
        """Simple similarity check."""
        # Check if one is substring of other or vice versa
        if str2 in str1 or str1 in str2:
            return True
        
        # Check edit distance for short strings (simplified)
        if abs(len(str1) - len(str2)) > 3:
            return False
        
        # Count matching characters
        matches = sum(1 for a, b in zip(str1, str2) if a == b)
        min_len = min(len(str1), len(str2))
        
        if min_len > 0 and matches / min_len >= 0.7:
            return True
        
        return False
