import re
from bs4 import BeautifulSoup

class HtmlProcessor:
    @staticmethod
    def clean_text(text):
        """Remove excessive whitespace and normalize line breaks."""
        # Replace multiple whitespace with a single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    @staticmethod
    def extract_main_content(html):
        """
        Extract the main content from HTML, removing navigation, ads, etc.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        unwanted_tags = ['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
                
        # Remove elements with common ad/nav class names
        unwanted_classes = ['ad', 'ads', 'advertisement', 'banner', 'nav', 'navbar', 'sidebar', 'comments']
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=lambda x: x and class_name in x.lower()):
                element.decompose()
        
        # Get the main content (heuristic: largest text block is likely the main content)
        main_content = ""
        if soup.main:
            main_content = soup.main.get_text()
        elif soup.article:
            main_content = soup.article.get_text()
        elif soup.find(id="content"):
            main_content = soup.find(id="content").get_text()
        elif soup.find(class_="content"):
            main_content = soup.find(class_="content").get_text()
        else:
            # Fallback: get text from all paragraphs
            main_content = ' '.join([p.get_text() for p in soup.find_all('p')])
            
        return HtmlProcessor.clean_text(main_content)
    
    @staticmethod
    def summarize_text(text, max_length=1000):
        """
        Truncate text to a maximum length, preserving sentences.
        
        Args:
            text: The text to summarize
            max_length: Maximum length in characters
            
        Returns:
            Summarized text
        """
        if len(text) <= max_length:
            return text
        
        # Find the last sentence boundary before max_length
        text = text[:max_length]
        last_sentence_end = max(
            text.rfind('.'), 
            text.rfind('!'), 
            text.rfind('?')
        )
        
        if last_sentence_end > 0:
            return text[:last_sentence_end + 1]
        return text