import time
import os
import json
import asyncio
import random 
import traceback 
import threading
from src.web_scraper.google_scraper import GoogleScraperPlaywright

class SearchEngine:
    def __init__(self, llm_client, config=None):
        """
        Initialize the search engine with the given LLM client and configuration.
        
        Args:
            llm_client: The LLM client to use for query processing and answer generation
            config: Configuration dictionary
        """
        self.llm_client = llm_client
        self.config = config or {}
        self.scraper = None
        self.event_loop = None
        
        # Add URL tracking to avoid duplicate fetching
        self.processed_urls = set()
        
        # Initialize the scraper
        self._initialize_scraper()
    
    def _initialize_scraper(self):
        """Initialize the Playwright scraper in a dedicated thread."""
        if hasattr(self, 'scraper_thread') and self.scraper_thread.is_alive():
            print("Browser thread is already running")
            return
        
        def run_async_init():
            """Run async initialization in a separate thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.event_loop = loop
            
            try:
                # Initialize the scraper
                self.scraper = GoogleScraperPlaywright()
                loop.run_until_complete(self.scraper.initialize())
                print("Browser initialized successfully")
            except Exception as e:
                print(f"Error initializing browser: {e}")
                self.scraper = None
        
        # Create and start a dedicated thread for the scraper
        self.scraper_thread = threading.Thread(target=run_async_init)
        self.scraper_thread.daemon = True
        self.scraper_thread.start()
        self.scraper_thread.join()  # Wait for initialization to complete
    
    def cleanup(self):
        """Close the browser and clean up resources."""
        if self.scraper and self.event_loop:
            try:
                self.event_loop.run_until_complete(self.scraper.close())
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")
        
    def clarify_query(self, query):
        """
        Check if the query needs clarification, get user input if needed,
        and always return an improved research question.
        """
        clarification = self.llm_client.get_query_clarification(query)
        
        # Case 1: Query needs clarification
        if clarification.get("needs_clarification", False) and clarification.get("questions", []):
            print("\n=== Query Clarification ===")
            print("To better understand your query, I have a few questions:")
            
            # Collect clarification responses
            clarification_responses = []
            for i, question in enumerate(clarification["questions"]):
                print(f"{i+1}. {question}")
                answer = input(f"Your response to question {i+1}: ")
                clarification_responses.append({"question": question, "answer": answer})
            
            print("\nThank you for the clarification! Generating improved research question...")
            
            # Generate improved query with LLM based on clarifications
            improved_query = self.llm_client.generate_improved_query(
                original_query=query,
                clarification_responses=clarification_responses
            )
            
            print(f"Improved research question: {improved_query}")
            return improved_query, query  # Return both improved and original
        
        # Case 2: No clarification needed, but still improve the query
        else:
            print("Generating improved research question...")
            
            # Generate improved query with LLM without clarifications
            improved_query = self.llm_client.generate_improved_query(
                original_query=query,
                clarification_responses=[]  # Empty list since no clarifications
            )
            
            print(f"Improved research question: {improved_query}")
            return improved_query, query

    async def perform_search_async(self, query, num_results=10):
        """Async version of perform_search that can be awaited."""
        search_query = self.llm_client.generate_search_query(query)
        print(f"Search query: {search_query}")
        
        # Check if scraper is initialized
        if not self.scraper:
            print("Reinitializing browser...")
            self._initialize_scraper()
            if not self.scraper:
                print("Failed to initialize browser. Cannot perform search.")
                return []
        
        # Perform web search with the optimized query
        try:
            # Create a new page/tab for each search
            results = await self.scraper.search_google(search_query, num_results, new_context=True)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def perform_search(self, query, num_results=10):
        """Synchronous wrapper for perform_search_async."""
        if not hasattr(self, 'event_loop') or self.event_loop is None:
            # Create an event loop if needed
            self.event_loop = asyncio.new_event_loop()
        
        # Run the async function in the event loop
        return self.event_loop.run_until_complete(
            self.perform_search_async(query, num_results)
        )
        
    # def perform_search(self, query, num_results=10):
    #     """Generate optimized search query and perform search."""
    #     search_query = self.llm_client.generate_search_query(query)
    #     print(f"Search query: {search_query}")
        
    #     # Check if scraper is initialized
    #     if not self.scraper:
    #         print("Reinitializing browser...")
    #         self._initialize_scraper()
    #         if not self.scraper:
    #             print("Failed to initialize browser. Cannot perform search.")
    #             return []
        
    #     # Perform web search with the optimized query
    #     print(f"Searching the web using Playwright browser...")
    #     try:
    #         results = self.event_loop.run_until_complete(
    #             self.scraper.search_google(search_query, num_results=num_results)
    #         )
    #         return results
    #     except Exception as e:
    #         print(f"Error during search: {e}")
    #         # Try to recover by reinitializing
    #         self._initialize_scraper()
    #         return []
        
    def fetch_content(self, enhanced_query, results, max_results=3, concurrent_fetches=5):
        """
        Fetch detailed content and analyze pages concurrently, processing each site immediately.
        
        Args:
            enhanced_query: The user's enhanced query for relevance analysis
            results: List of search results
            max_results: Maximum number of results to fetch content for
            concurrent_fetches: Number of concurrent pages to fetch
            
        Returns:
            Tuple of (processed_results, newly_processed_urls)
        """
        # Check if scraper is initialized
        if not self.scraper:
            print("Reinitializing browser...")
            self._initialize_scraper()
            if not self.scraper:
                print("Failed to initialize browser. Cannot fetch content.")
                return results, []
        
        # Filter to top results, skipping already processed URLs
        top_results = []
        skipped_count = 0
        newly_processed_urls = []  # Add this to track URLs
        
        for result in results:
            url = result.get('url', '')
            if not url or not url.startswith('http'):
                continue
                
            # Skip already processed URLs
            if url in self.processed_urls:
                print(f"Skipping already processed URL: {url}")
                skipped_count += 1
                continue
                
            top_results.append(result)
            if len(top_results) >= max_results:
                break
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} already processed URLs")
        
        if not top_results:
            print("No new URLs to process")
            return results, []
            
        print(f"Processing {len(top_results)} results with concurrent fetch and analysis...")
        
        # Define async function for concurrent processing
        async def fetch_and_analyze_all():
            """Fetch and analyze content concurrently, processing each result as soon as it's ready."""
            # Create a new empty list to hold processed results
            processed_results = []
            
            # Define an async helper function that processes a single result
            async def process_single_result(result):
                try:
                    url = result.get('url', '')
                    title = result.get('title', 'Untitled')
                    
                    # Mark URL as processed before fetching
                    self.processed_urls.add(url)
                    newly_processed_urls.append(url)  # Add this line
                    
                    print(f"🌐 Fetching: {title}")
                    # Fetch the content
                    content = await self.scraper.fetch_page_content_humanlike(url)
                    
                    # If we get here, fetch was successful
                    print(f"✅ Fetched {title} ({len(content)} chars)")
                    result['content'] = content
                    
                    # Immediately analyze the content
                    print(f"🧠 Analyzing: {title}")
                    try:
                        page_analysis = self.llm_client.generate_page_understanding(
                            enhanced_query=enhanced_query,
                            content=content,
                            url=url,
                            title=title
                        )
                        
                        # Store the analysis
                        result['page_analysis'] = page_analysis
                        
                        # Display the analysis feedback
                        print(f"📊 Analysis complete for {title} (Relevance: {page_analysis['relevance_score']}/10)")
                        print(f"   {page_analysis['summary'][:150]}...")
                        print(f"   Key points: {', '.join(point[:30] + '...' for point in page_analysis['key_points'][:2])}")
                        
                    except Exception as e:
                        print(f"⚠️ Error analyzing {title}: {e}")
                        result['page_analysis'] = {
                            "summary": "Error during content analysis",
                            "relevance_score": 5,
                            "key_points": ["Analysis failed due to an error"]
                        }
                    
                    # Add the fully processed result to our list
                    processed_results.append(result)
                    
                except Exception as e:
                    print(f"❌ Error processing {result.get('url', 'unknown URL')}: {e}")
                    # Handle the error case
                    result['content'] = result.get('snippet', '')
                    result['page_analysis'] = {
                        "summary": "Failed to analyze page content",
                        "relevance_score": 0,
                        "key_points": []
                    }
                    processed_results.append(result)
            
            # Create tasks for all results and run them concurrently
            tasks = []
            for i in range(0, len(top_results), concurrent_fetches):
                batch = top_results[i:min(i+concurrent_fetches, len(top_results))]
                print(f"Processing batch {i//concurrent_fetches + 1} ({len(batch)} pages)...")
                batch_tasks = [process_single_result(result) for result in batch]
                tasks.extend(batch_tasks)
                await asyncio.gather(*batch_tasks)
                
                if i + concurrent_fetches < len(top_results):
                    delay = random.uniform(1.0, 2.0)
                    print(f"Waiting {delay:.1f}s before next batch...")
                    await asyncio.sleep(delay)
            
            return processed_results, newly_processed_urls
            
        try:
            # Run the async function
            processed_results, _ = self.event_loop.run_until_complete(fetch_and_analyze_all())
            
            # Determine how many fetches were successful
            successful_count = sum(1 for r in processed_results if r.get('page_analysis', {}).get('relevance_score', 0) > 0)
            print(f"Content processing complete: {successful_count}/{len(processed_results)} successful")
            
            # Return the enhanced results AND newly processed URLs
            return processed_results, newly_processed_urls
            
        except Exception as e:
            print(f"Error during content processing: {e}")
            traceback.print_exc()
            
            # Create fallback responses for all results
            for result in top_results:
                result['content'] = result.get('snippet', '')
                result['page_analysis'] = {
                    "summary": "Content fetching failed",
                    "relevance_score": 0,
                    "key_points": []
                }
            
            # Always return a tuple of (results, urls)
            return top_results, newly_processed_urls
        
    async def fetch_content_async(self, enhanced_query, results, max_results=3, concurrent_fetches=5, already_processed_urls=None):
        """
        Async version of fetch_content - Fetch detailed content and analyze pages concurrently.
        
        Args:
            enhanced_query: The user's enhanced query for relevance analysis
            results: List of search results
            max_results: Maximum number of results to fetch content for
            concurrent_fetches: Number of concurrent pages to fetch
            already_processed_urls: Optional list of additional URLs to consider already processed
            
        Returns:
            Tuple of (processed_results, newly_processed_urls)
        """
        # Check if scraper is initialized
        if not self.scraper:
            print("Reinitializing browser...")
            self._initialize_scraper()
            if not self.scraper:
                print("Failed to initialize browser. Cannot fetch content.")
                return results, []
        
        # Combine internal processed URLs with passed list
        all_processed_urls = set(self.processed_urls)
        if already_processed_urls:
            all_processed_urls.update(already_processed_urls)
        
        # Filter to top results, skipping already processed URLs
        top_results = []
        skipped_count = 0
        
        for result in results:
            url = result.get('url', '')
            if not url or not url.startswith('http'):
                continue
                
            # Skip already processed URLs
            if url in all_processed_urls:
                print(f"Skipping already processed URL: {url}")
                skipped_count += 1
                continue
                
            top_results.append(result)
            if len(top_results) >= max_results:
                break
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} already processed URLs")
        
        if not top_results:
            print("No new URLs to process")
            return results, []
            
        print(f"Processing {len(top_results)} results with concurrent fetch and analysis...")
        
        # Create a new empty list to hold processed results
        processed_results = []
        # Track newly processed URLs
        newly_processed_urls = []
        
        # Define an async helper function that processes a single result
        async def process_single_result(result):
            try:
                url = result.get('url', '')
                title = result.get('title', 'Untitled')
                
                # Mark URL as processed before fetching
                self.processed_urls.add(url)
                newly_processed_urls.append(url)
                
                print(f"🌐 Fetching: {title}")
                # Fetch the content
                content = await self.scraper.fetch_page_content_humanlike(url)
                
                # If we get here, fetch was successful
                print(f"✅ Fetched {title} ({len(content)} chars)")
                result['content'] = content
                
                # Immediately analyze the content
                print(f"🧠 Analyzing: {title}")
                try:
                    page_analysis = self.llm_client.generate_page_understanding(
                        enhanced_query=enhanced_query,
                        content=content,
                        url=url,
                        title=title
                    )
                    
                    # Store the analysis
                    result['page_analysis'] = page_analysis
                    
                    # Display the analysis feedback
                    print(f"📊 Analysis complete for {title} (Relevance: {page_analysis['relevance_score']}/10)")
                    print(f"   {page_analysis['summary'][:150]}...")
                    print(f"   Key points: {', '.join(point[:30] + '...' for point in page_analysis['key_points'][:2])}")
                    
                except Exception as e:
                    print(f"⚠️ Error analyzing {title}: {e}")
                    result['page_analysis'] = {
                        "summary": "Error during content analysis",
                        "relevance_score": 5,
                        "key_points": ["Analysis failed due to an error"]
                    }
                
                # Add the fully processed result to our list
                processed_results.append(result)
                
            except Exception as e:
                print(f"❌ Error processing {result.get('url', 'unknown URL')}: {e}")
                # Handle the error case
                result['content'] = result.get('snippet', '')
                result['page_analysis'] = {
                    "summary": "Failed to analyze page content",
                    "relevance_score": 0,
                    "key_points": []
                }
                processed_results.append(result)
        
        try:
            # Process batches
            for i in range(0, len(top_results), concurrent_fetches):
                batch = top_results[i:min(i+concurrent_fetches, len(top_results))]
                print(f"Starting batch {i//concurrent_fetches + 1}/{(len(top_results)-1)//concurrent_fetches + 1} ({len(batch)} pages)...")
                
                # Create tasks for this batch and run them concurrently
                tasks = [process_single_result(result) for result in batch]
                await asyncio.gather(*tasks)
                
                # Add delay between batches
                if i + concurrent_fetches < len(top_results):
                    delay_time = random.uniform(1.0, 2.0)
                    print(f"Waiting {delay_time:.1f}s before next batch...")
                    await asyncio.sleep(delay_time)
            
            # Determine how many fetches were successful
            successful_count = sum(1 for r in processed_results if r.get('page_analysis', {}).get('relevance_score', 0) > 0)
            print(f"Content processing complete: {successful_count}/{len(processed_results)} successful")
            
            # Return both the processed results and newly processed URLs
            return processed_results, newly_processed_urls
            
        except Exception as e:
            print(f"Error during content processing: {e}")
            traceback.print_exc()
            
            # Create fallback responses for all results
            for result in top_results:
                result['content'] = result.get('snippet', '')
                result['page_analysis'] = {
                    "summary": "Content fetching failed",
                    "relevance_score": 0,
                    "key_points": []
                }
            
            return top_results, newly_processed_urls
    
    def generate_intermediate_answer(self, query, results):
        """Generate an intermediate answer based on current results."""
        return self.llm_client.generate_answer(query, results, is_final=False)
        
    def generate_follow_up_queries(self, original_query, results, max_queries=2):
        """Generate follow-up queries for the next iteration."""
        return self.llm_client.generate_follow_up_queries(original_query, results, max_queries=max_queries)
        
    def generate_final_answer(self, original_query, all_results, intermediate_understandings=None):
        """
        Generate a final comprehensive answer with follow-up questions,
        incorporating intermediate understandings.
        """
        if not intermediate_understandings:
            intermediate_understandings = []
        
        # Format the intermediate understandings
        formatted_understandings = ""
        if intermediate_understandings:
            formatted_understandings = "\n\nIntermediate Understandings:\n" + "\n".join([
                f"Iteration {item['iteration']} ({item['query']}):\n{item['understanding']}\n"
                for item in intermediate_understandings
            ])
        
        # Call the LLM with both results and intermediate understandings
        return self.llm_client.generate_answer_in_multiple_stages(
            original_query, 
            all_results, 
            intermediate_understandings
        )
        
    def save_results(self, original_query, max_iterations, final_result, all_results, intermediate_understandings=None):
        """Save search results to a JSON file."""
        try:
            results_dir = self.config.get('paths', {}).get('results_dir', 'results')
            # Convert relative path to absolute if needed
            if not os.path.isabs(results_dir):
                results_dir = os.path.join(os.path.dirname(__file__), '..', '..', results_dir)
                
            os.makedirs(results_dir, exist_ok=True)
            
            filename = f"search_{time.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(results_dir, filename)
            
            # Save as structured JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json_data = {
                    "query": original_query,
                    "iterations": max_iterations,
                    "answer": final_result["answer"],
                    "follow_up_questions": final_result["follow_up_questions"],
                    "intermediate_understandings": intermediate_understandings or [],
                    "sources": [
                        {
                            "title": result.get("title", "No title"),
                            "url": result.get("url", ""),
                            "snippet": result.get("snippet", "")[:200],
                            # Add page analysis if available
                            "page_analysis": result.get("page_analysis", {
                                "summary": "No analysis available",
                                "relevance_score": 0,
                                "key_points": []
                            })
                        }
                        for result in all_results if result.get("url")
                    ]
                }
                json.dump(json_data, f, indent=2)
            
            return filepath
        except Exception as e:
            print(f"Error saving results: {e}")
            return None
        

    def save_results_with_html(self, original_query, max_iterations, final_result, all_results, intermediate_understandings=None):
        """Save search results to a JSON file and generate an HTML presentation."""
        try:
            # First save the JSON results as before
            json_filepath = self.save_results(original_query, max_iterations, final_result, all_results, intermediate_understandings)
            
            if not json_filepath:
                return None
                
            # Now generate HTML
            try:
                from src.utils.html_generator import generate_html_from_result
                html_filepath = generate_html_from_result(json_filepath)
                return html_filepath
            except ImportError:
                print("HTML generator not available. Install markdown package with: pip install markdown")
                return json_filepath
                
        except Exception as e:
            print(f"Error saving results with HTML: {e}")
            return None