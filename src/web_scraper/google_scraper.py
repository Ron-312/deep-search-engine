import asyncio
import os
import random
import time
from urllib.parse import quote_plus

class GoogleScraperPlaywright:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize the browser with stealth settings."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            
            # Change headless to False to make the browser visible
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Changed from True to False to make browser visible
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    # Additional arguments to help with detection avoidance
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--disable-automation',
                    '--disable-internal-flash',
                    '--disable-notifications'
                ]
            )
            
            # The rest of the method remains the same...
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                has_touch=False,
                is_mobile=False,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation', 'notifications'],
                accept_downloads=True
            )
            
            # Add even more anti-detection measures
            await self.context.add_init_script("""
                // Override the navigator.webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
                
                // Add chrome object for more browser-like behavior
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {
                        isInstalled: false,
                    },
                };
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        },
                        {
                            0: {type: "application/x-nacl"},
                            description: "Native Client Executable",
                            filename: "internal-nacl-plugin",
                            length: 1,
                            name: "Native Client"
                        }
                    ],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Disable permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """)
            
            self.page = await self.context.new_page()
            return True
        except ImportError:
            print("ERROR: Playwright not installed. Please install with: pip install playwright")
            print("Then run: playwright install")
            return False
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            return False
    
    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def human_like_typing(self, selector, text):
        """Type text like a human with random delays between keystrokes."""
        await self.page.focus(selector)
        
        for char in text:
            await self.page.type(selector, char, delay=random.randint(100, 200))
            await asyncio.sleep(random.uniform(0.01, 0.03))
    
    async def random_mouse_movement(self):
        """Move the mouse in a somewhat random pattern to simulate human behavior."""
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 700)
            await self.page.mouse.move(x, y, steps=random.randint(5, 10))
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def search_google(self, query, num_results=10, new_context=False):
        """
        Search Google and return the search results with stealth measures.
        
        Args:
            query: The search query
            num_results: Number of results to collect
            new_context: If True, create a new browser context for this search
            
        Returns:
            A list of dictionaries with title, url, and snippet
        """
        # Create a new context and page if requested
        page = None
        context = None
        if new_context:
            try:
                # Create new context with the same settings
                context = await self.browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    has_touch=False,
                    is_mobile=False,
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation', 'notifications'],
                    accept_downloads=True
                )
                
                # Add anti-detection script
                await context.add_init_script("""
                    // Override the navigator.webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                    
                    // Add chrome object for more browser-like behavior
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {
                            isInstalled: false,
                        },
                    };
                    
                    // Override plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {
                                0: {type: "application/x-google-chrome-pdf"},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf"},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            },
                            {
                                0: {type: "application/x-nacl"},
                                description: "Native Client Executable",
                                filename: "internal-nacl-plugin",
                                length: 1,
                                name: "Native Client"
                            }
                        ],
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Disable permissions API
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                    );
                """)
                
                page = await context.new_page()
            except Exception as e:
                print(f"Error creating new context: {e}")
                return []
        else:
            # Use existing page
            if not self.page:
                success = await self.initialize()
                if not success:
                    return []
            page = self.page
        
        try:
            # Navigate to Google
            await page.goto('https://www.google.com/', wait_until='networkidle')
            
            # Random delay to seem more human-like
            await asyncio.sleep(random.uniform(1, 2))
            
            # IMPORTANT: Use the correct page object for all operations
            
            # Move mouse randomly before interactions
            if new_context:
                # Using the new page
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, 1200)
                    y = random.randint(100, 700)
                    await page.mouse.move(x, y, steps=random.randint(5, 10))
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            else:
                # Using the default page
                await self.random_mouse_movement()
            
            # Accept cookies if prompted
            try:
                accept_button = await page.query_selector('button:has-text("Accept all")')
                if accept_button:
                    await accept_button.click()
                    await asyncio.sleep(random.uniform(0.5, 1))
            except Exception as e:
                print(f"Cookie notice handling error: {e}")
                # Continue anyway
            
            # Type query like a human
            if new_context:
                # Type on the new page
                await page.focus('[name="q"]')
                for char in query:
                    await page.type('[name="q"]', char, delay=random.randint(100, 200))
                    await asyncio.sleep(random.uniform(0.01, 0.03))
            else:
                # Use existing method on default page
                await self.human_like_typing('[name="q"]', query)
            
            # Random delay before pressing Enter
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # Press Enter and wait for results
            await page.press('[name="q"]', 'Enter')
            
            # Wait for results to load
            try:
                await page.wait_for_selector('div#search', timeout=10000)
            except:
                # Try alternative selector if the first one fails
                await page.wait_for_selector('div#main', timeout=10000)
            
            # Random delay before extracting results
            await asyncio.sleep(random.uniform(1, 2))
            
            # Scroll down randomly to load more results
            for _ in range(random.randint(2, 4)):
                await page.evaluate('window.scrollBy(0, Math.floor(Math.random() * 600) + 300)')
                await asyncio.sleep(random.uniform(0.3, 0.7))
            
            # Extract search results
            results = []
            
            # Get all search result items - try multiple selectors
            search_results = None
            selectors = [
                '#search div.g',
                '#search > div > div > div',
                '#main > div > div > div > div',
                '#search .MjjYud' # newer Google layout
            ]
            
            for selector in selectors:
                search_results = await page.query_selector_all(selector)
                if search_results and len(search_results) > 0:
                    break
            
            if not search_results or len(search_results) == 0:
                print("Could not find search results with known selectors.")
                return []
            
            for i, result in enumerate(search_results):
                if i >= num_results:
                    break
                    
                try:
                    # Try to find title element with multiple possible selectors
                    title_elem = None
                    for title_selector in ['h3', '.LC20lb', '.DKV0Md']:
                        title_elem = await result.query_selector(title_selector)
                        if title_elem:
                            break
                    
                    # Find URL
                    a_elem = await result.query_selector('a')
                    
                    # Find snippet with multiple possible selectors
                    snippet_elem = None
                    for snippet_selector in ['div.VwiC3b', '.yXK7lf', '.lEBKkf', '[data-content-feature="1"]']:
                        snippet_elem = await result.query_selector(snippet_selector)
                        if snippet_elem:
                            break
                    
                    # Skip if essential elements not found
                    if not title_elem or not a_elem:
                        continue
                    
                    title = await title_elem.inner_text() if title_elem else "No title"
                    url = await a_elem.get_attribute('href') if a_elem else ""
                    snippet = await snippet_elem.inner_text() if snippet_elem else "No snippet"
                    
                    # Skip non-http URLs or empty titles
                    if not url or not url.startswith('http') or not title:
                        continue
                    
                    # Skip duplicate URLs
                    if any(r.get('url') == url for r in results):
                        continue
                    
                    results.append({
                        "id": f"result_{i+1}",
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "score": float(num_results - i) / num_results  # Simple scoring
                    })
                except Exception as e:
                    print(f"Error extracting result {i}: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error during Google search: {e}")
            # Screenshot for debugging
            try:
                await page.screenshot(path=f"google_error_{query[:10].replace(' ', '_')}.png")
                print(f"Screenshot saved")
            except:
                pass
            return []
        
        finally:
            # Clean up new context if we created one
            if new_context and context:
                try:
                    await context.close()
                    print("Closed temporary browser context")
                except Exception as e:
                    print(f"Error closing context: {e}")

    async def fetch_page_content_humanlike(self, url, max_retries=2):
        """
        Fetch page content with human-like behavior for all domains.
        """
        # Create a new page for each request to avoid cross-site tracking
        page = await self.context.new_page()
        
        try:
            print(f"Fetching content from {url} with human-like behavior...")
            
            # Random pre-navigation delay (like a human thinking)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # First navigate to a search engine or referring site (like a human would come from)
            referrers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.reddit.com/",
                "https://twitter.com/"
            ]
            await page.goto(random.choice(referrers), wait_until='domcontentloaded')
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # Set a random viewport size (different monitor sizes)
            viewports = [
                {'width': 1366, 'height': 768},  # Common laptop
                {'width': 1920, 'height': 1080}, # Full HD
                {'width': 1440, 'height': 900},  # MacBook
                {'width': 1536, 'height': 864}   # Common Windows size
            ]
            await page.set_viewport_size(random.choice(viewports))
            
            # Now navigate to the actual URL
            for attempt in range(max_retries):
                try:
                    # Use different navigation strategies on retries
                    if attempt == 0:
                        response = await page.goto(url, timeout=7000, wait_until='domcontentloaded')
                    else:
                        # Try a different approach on retry
                        response = await page.goto(url, timeout=10000, wait_until='commit')
                    
                    # Check response status
                    if response and response.status >= 400:
                        print(f"Received HTTP {response.status} for {url}")
                        if attempt < max_retries - 1:
                            print(f"Will retry ({attempt+1}/{max_retries})...")
                            await asyncio.sleep(random.uniform(1, 2))
                            continue
                    
                    # Successfully loaded page, now act human-like
                    
                    # Wait for page to stabilize
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # Handle cookie consent dialogs and popups
                    await self._handle_common_popups(page)
                    
                    # Scroll like a human would (varying speed and pauses)
                    await self._human_like_scrolling(page)
                    
                    # Maybe hover over some links randomly
                    await self._random_interactions(page)
                    
                    # Replace the current content extraction with:
                    content = await self.extract_content_with_readability(page)
                    
                    # Clean the extracted content
                    content = await self.clean_extracted_content(content)
    
                    
                    # Truncate and return the content
                    max_length = 12000
                    if len(content) > max_length:
                        return content[:max_length] + "... [content truncated]"
                    
                    return content
                    
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {url}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        # Try with a different approach on next attempt
                        print("Retrying with modified approach...")
                        
                        # Clear cookies, change user agent
                        await page.context.clear_cookies()
                        
                        # Wait longer between retries
                        await asyncio.sleep(random.uniform(2, 3))
        
        except Exception as e:
            print(f"All attempts failed for {url}: {str(e)}")
            # Try simple requests fallback
            try:
                print(f"Trying simple HTTP request fallback for {url}")
                import requests
                from bs4 import BeautifulSoup
                
                # Rotate user agents
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
                ]
                
                headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://www.google.com/",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "cross-site",
                    "Cache-Control": "max-age=0"
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                
                # Get text and clean it
                text = soup.get_text(separator='\n')
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)
                
                # Truncate if needed
                max_length = 12000
                if len(text) > max_length:
                    return text[:max_length] + "... [content truncated]"
                
                return text
                
            except Exception as req_error:
                print(f"HTTP fallback also failed: {str(req_error)}")
                return f"Could not extract content from {url} (all methods failed)"
        
        finally:
            # Always close the page to free resources
            try:
                await page.close()
            except:
                pass

    async def extract_content_with_readability(self, page):
        """Extract main content using a Readability-like algorithm."""
        return await page.evaluate('''() => {
            // Function to implement core readability heuristics
            function getReadableContent() {
                // Potential content containers by importance
                const CONTENT_SELECTORS = [
                    'article', '[role="main"]', '.post-content', '.article-content', '.entry-content',
                    '.content', 'main', '#main', '#content', '.main', '.post', '.article'
                ];
                
                // Find the best content container
                let mainContent = null;
                for (const selector of CONTENT_SELECTORS) {
                    const element = document.querySelector(selector);
                    if (element) {
                        // Check if this element has substantial text
                        const textLength = element.textContent.trim().length;
                        if (textLength > 250) {
                            mainContent = element;
                            break;
                        }
                    }
                }
                
                // If no main content container found, find the element with most paragraph content
                if (!mainContent) {
                    const paragraphs = document.querySelectorAll('p');
                    const contentMap = new Map();
                    
                    // Group paragraphs by parent to find the container with most paragraph content
                    paragraphs.forEach(p => {
                        // Skip very short paragraphs
                        if (p.textContent.trim().length < 20) return;
                        
                        let parent = p.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            // Add to content map
                            contentMap.set(parent, (contentMap.get(parent) || 0) + p.textContent.length);
                            parent = parent.parentElement;
                        }
                    });
                    
                    // Find the parent with most content
                    let maxContent = 0;
                    contentMap.forEach((content, element) => {
                        if (content > maxContent) {
                            maxContent = content;
                            mainContent = element;
                        }
                    });
                }
                
                // If still no main content, use the body
                if (!mainContent) {
                    mainContent = document.body;
                }
                
                return mainContent;
            }
            
            // Get the main content container
            const mainContent = getReadableContent();
            
            // Clone it to avoid modifying the original
            const contentClone = mainContent.cloneNode(true);
            
            // Remove unwanted elements from the clone - FIX: put all selectors on one line
            const elementsToRemove = contentClone.querySelectorAll('script, style, iframe, nav, header, footer, aside, [role="banner"], [role="navigation"], [role="complementary"], form, .ad, .ads, .advertisement, .banner, .social, .share, .comments, .comment-form, #comments, .sidebar, .footer, [class*="cookie"], [id*="cookie"]');
            
            elementsToRemove.forEach(el => el.remove());
            
            // Extract headings for structure
            const headings = contentClone.querySelectorAll('h1, h2, h3, h4, h5, h6');
            const headingTexts = Array.from(headings).map(h => `${h.tagName}: ${h.textContent.trim()}`);
            
            // Extract paragraphs (the main content)
            const paragraphs = contentClone.querySelectorAll('p');
            const paragraphTexts = Array.from(paragraphs)
                .filter(p => p.textContent.trim().length > 0)
                .map(p => p.textContent.trim());
            
            // Extract lists for structure
            const listItems = contentClone.querySelectorAll('li');
            const listTexts = Array.from(listItems).map(li => `• ${li.textContent.trim()}`);
            
            // Get image alt text for context - but only for meaningful images, not UI elements
            const images = contentClone.querySelectorAll('img[alt]');
            const imageTexts = Array.from(images)
                .filter(img => {
                    // Skip images that are likely UI elements
                    const alt = img.alt.trim().toLowerCase();
                    
                    // Skip small images (likely icons)
                    const isSmallImage = (img.width < 100 || img.height < 100) && img.width > 0 && img.height > 0;
                    
                    // Skip images with typical UI element descriptions
                    const isUIElement = alt.includes('icon') || alt.includes('logo') || 
                                    alt.includes('button') || alt.includes('arrow') ||
                                    alt.includes('banner') || alt.includes('avatar') ||
                                    alt.includes('badge') || alt.includes('menu');
                                    
                    // Skip images with very short alt text
                    const isTooShort = alt.length < 10;
                    
                    // Skip images that are probably not informative
                    return !(isSmallImage || isUIElement || isTooShort);
                })
                .map(img => `[Image: ${img.alt.trim()}]`);

            // Build structured text content
            let structuredContent = '';

            // Only add the IMAGES section if we have meaningful images
            if (imageTexts.length > 0) {
                structuredContent += `IMAGES:\\n${imageTexts.join('\\n')}\\n\\n`;
            }

            // Add page title first
            const pageTitle = document.title;
            structuredContent += `TITLE: ${pageTitle}\\n\\n`;
            
            // Add extracted headings
            if (headingTexts.length > 0) {
                structuredContent += `DOCUMENT STRUCTURE:\\n${headingTexts.join('\\n')}\\n\\n`;
            }
            
            // Add main content (paragraphs)
            structuredContent += `MAIN CONTENT:\\n${paragraphTexts.join('\\n\\n')}\\n\\n`;
            
            // Add lists if present
            if (listTexts.length > 0) {
                structuredContent += `LISTS:\\n${listTexts.join('\\n')}\\n\\n`;
            }
            
            return structuredContent.trim();
        }''')
        
    async def clean_extracted_content(self, content):
        """Apply advanced cleaning to extracted content."""
        # Handle in Python rather than JavaScript for more control
        import re
        
        # Remove entire IMAGES section and all image references
        # Remove the entire IMAGES section
        content = re.sub(r'IMAGES:[\s\S]*?(?=\n\n|\Z)', '', content)
        
        # Remove any remaining image references in the text
        content = re.sub(r'\[Image:[^\]]*\]', '', content)
        
        # Remove email addresses to protect privacy
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
        
        # Remove phone numbers
        content = re.sub(r'\b(\+\d{1,2}\s?)?(\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', content)
        
        # Remove common noise phrases
        noise_phrases = [
            'accept cookies', 'cookie policy', 'privacy policy', 'terms of service',
            'all rights reserved', 'copyright', 'sign up for our newsletter',
            'share this article', 'follow us on', 'subscribe to', 'login', 'sign in',
            'create account', 'powered by', 'advertisement', 'sponsored'
        ]
        
        for phrase in noise_phrases:
            content = re.sub(r'(?i)\b' + re.escape(phrase) + r'\b.*?\n', '', content)
        
        # Fix extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r'\s{2,}', ' ', content)
        
        # Remove URLs in text unless they appear to be citations
        content = re.sub(r'https?://(?!(?:www\.)?(?:doi\.org|dx\.doi\.org))[^\s]+', '[URL]', content)
        
        return content.strip()

    async def _handle_common_popups(self, page):
        """Handle common popups and consent dialogs."""
        try:
            # List of common popup/consent button selectors
            popup_selectors = [
                'button:has-text("Accept")', 
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                'button:has-text("Accept Cookies")',
                'button:has-text("Allow")',
                'button:has-text("Allow All")',
                'button:has-text("Agree")',
                'button:has-text("I Agree")',
                'button:has-text("Continue")',
                'button:has-text("Close")',
                'button:has-text("Got It")',
                'button:has-text("OK")',
                '.cc-accept',
                '.accept-cookies',
                '#accept-cookies',
                '[aria-label="Accept cookies"]',
                '[data-testid="cookie-policy-dialog-accept-button"]'
            ]
            
            for selector in popup_selectors:
                try:
                    # Check if element exists with short timeout
                    popup_btn = await page.wait_for_selector(selector, timeout=1000)
                    if popup_btn:
                        # Move mouse to button like a human would
                        await popup_btn.hover()
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        await popup_btn.click()
                        print("Handled popup/consent dialog")
                        await asyncio.sleep(random.uniform(0.5, 1))
                        break
                except:
                    continue
                    
        except Exception as e:
            # Don't stop execution for popup handling errors
            print(f"Non-critical error while handling popups: {str(e)}")

    async def _human_like_scrolling(self, page):
        """Scroll the page like a human would."""
        try:
            # Get page height
            height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            # Calculate number of scrolls (don't always scroll to bottom)
            max_scroll = min(height, random.randint(3, 8) * viewport_height)
            scroll_count = random.randint(4, 10)
            
            for i in range(scroll_count):
                # Calculate variable scroll step (sometimes big, sometimes small)
                if i == 0:
                    # First scroll is usually smaller
                    scroll_step = random.randint(100, 300)
                else:
                    scroll_step = random.randint(200, viewport_height)
                
                # Variable scroll speed
                pixels_per_step = random.randint(10, 30)
                step_delay = random.uniform(0.005, 0.015)
                
                # Calculate target position
                current_position = await page.evaluate('window.pageYOffset')
                target_position = min(current_position + scroll_step, max_scroll)
                
                # Gradually scroll to target
                for pos in range(current_position, target_position, pixels_per_step):
                    await page.evaluate(f'window.scrollTo(0, {pos})')
                    await asyncio.sleep(step_delay)
                
                # Make sure we reach the target position
                await page.evaluate(f'window.scrollTo(0, {target_position})')
                
                # Pause between scrolls (sometimes longer, simulating reading)
                if random.random() < 0.3:  # 30% chance to pause longer (reading)
                    await asyncio.sleep(random.uniform(0.8, 2.5))
                else:
                    await asyncio.sleep(random.uniform(0.3, 0.8))
        
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
            # Continue with extraction even if scrolling fails

    async def _random_interactions(self, page):
        """Perform random interactions that a human might do."""
        try:
            # Only do this sometimes (30% chance)
            if random.random() > 0.3:
                return
                
            # Find some links or button elements
            elements = await page.query_selector_all('a, button')
            
            # Limit to a few interactions
            interact_count = min(len(elements), random.randint(1, 3))
            
            for i in range(interact_count):
                # Pick a random element
                if not elements:
                    break
                
                idx = random.randint(0, len(elements) - 1)
                elem = elements[idx]
                
                # Hover over it
                try:
                    await elem.hover()
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    
                    # Very rarely, click on the element
                    if random.random() < 0.1:
                        await elem.click()
                        await asyncio.sleep(random.uniform(0.5, 1))
                except:
                    continue
                
        except Exception as e:
            print(f"Error during random interactions: {str(e)}")
            # Continue with extraction even if interactions fail
