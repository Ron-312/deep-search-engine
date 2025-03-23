import time
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from .engine import SearchEngine

async def process_follow_up_query(engine, enhanced_query, idx, num_results=3, max_content=2):
    """Process a single follow-up query concurrently."""
    print(f"\nFollow-up query {idx+1}: {enhanced_query}")
    
    # Perform search with follow-up query
    query_results = await engine.perform_search_async(enhanced_query, num_results=num_results)
    
    if not query_results:
        print(f"No results found for follow-up query {idx+1}")
        return [], None
        
    # Display results
    print(f"Found {len(query_results)} results for follow-up query {idx+1}")
    for i, result in enumerate(query_results):
        print(f"{i+1}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   {result['snippet'][:100]}...\n")
    
    # Automatically fetch content
    print(f"Fetching content for follow-up query {idx+1}...")
    fetched_results = await engine.fetch_content_async(enhanced_query, query_results, max_results=max_content)
    
    # Generate understanding
    if fetched_results:
        print(f"Generating understanding for follow-up query {idx+1}...")
        understanding = engine.generate_intermediate_answer(enhanced_query, fetched_results)
        
        return fetched_results, {
            "iteration": idx + 2,  # +2 because first iteration is 1
            "query": enhanced_query,
            "understanding": understanding,
            "type": "follow-up"
        }
    
    return fetched_results, None

def interactive_search(llm_client, config=None):
    """Run an interactive search loop."""
    engine = SearchEngine(llm_client, config)
    max_results = config.get('search', {}).get('results_per_search', 5)
    content_fetch_limit = config.get('search', {}).get('content_fetch_limit', 3)
    
    try:
        print("\n=== Iterative Deep Search Engine ===")
        print("Type 'exit' to quit\n")
        
        while True:
            query = input("\nEnter your search query: ")
            if query.lower() in ('exit', 'quit'):
                break
            
            # Clarification step
            enhanced_query, original_query = engine.clarify_query(query)
            
            # Ask for number of search iterations
            try:
                default_iterations = config.get('search', {}).get('default_iterations', 2)
                max_allowed = config.get('search', {}).get('max_iterations', 5)
                
                max_iterations = int(input(f"How many search iterations? (1-{max_allowed}, default: {default_iterations}): ") or default_iterations)
                max_iterations = max(1, min(max_allowed, max_iterations))
            except ValueError:
                print(f"Invalid input. Using default of {default_iterations} iteration(s).")
                max_iterations = default_iterations
            
            # Keep track of all results and intermediate answers across iterations
            all_results = []
            intermediate_understandings = []
            
            # First iteration - use the original query
            print("\n=== Iteration 1 ===")
            print("Generating optimized search terms...")
            
            # Perform search
            results = engine.perform_search(enhanced_query, num_results=max_results)
            
            if not results:
                print("No results found.")
                continue
            
            # Display search results
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results):
                print(f"{i+1}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   {result['snippet'][:150]}...\n")
            
            # Fetch detailed content for first iteration
            results = engine.fetch_content(enhanced_query, results, max_results=content_fetch_limit)
            print("Detailed content fetched!")
            
            # Generate intermediate answer
            if max_iterations > 1:
                print("Generating intermediate understanding...")
                intermediate_answer = engine.generate_intermediate_answer(enhanced_query, results)
                intermediate_understandings.append({
                    "iteration": 1,
                    "query": enhanced_query,
                    "understanding": intermediate_answer,
                    "type": "initial"  # Add this type field
                })
                print("\n=== Intermediate Understanding ===")
                print(intermediate_answer)
                print("==================================")
            
            # Add results to our collection
            all_results.extend(results)
            
            # Additional iterations with follow-up queries
            for iteration in range(2, max_iterations + 1):
                print(f"\n=== Iteration {iteration} ===")
                
                # Generate follow-up queries based on current results
                print("Generating follow-up search queries...")
                follow_up_queries = engine.generate_follow_up_queries(enhanced_query, results, max_queries=2)
                
                # Process all follow-up queries concurrently
                iteration_results = []

                # Get the event loop from the engine
                loop = engine.event_loop

                # Create tasks explicitly with the engine's event loop
                tasks = [
                    loop.create_task(process_follow_up_query(engine, query, j, num_results=3, max_content=2))
                    for j, query in enumerate(follow_up_queries)
                ]

                # Run all tasks concurrently
                follow_up_results = loop.run_until_complete(asyncio.gather(*tasks))
                
                # Process results
                for results_batch, understanding in follow_up_results:
                    if results_batch:
                        iteration_results.extend(results_batch)
                        if understanding:
                            intermediate_understandings.append(understanding)
                            print(f"\n--- Follow-up Understanding ---")
                            print(understanding["understanding"])
                            print("------------------------------------")
                
                # Update results for next iteration
                all_results.extend(iteration_results)
                
                # Generate a consolidated intermediate answer for this entire iteration
                if iteration_results:
                    print(f"\nGenerating consolidated understanding for iteration {iteration}...")
                    # Use the original query but with all results from this iteration
                    consolidated_understanding = engine.generate_intermediate_answer(
                        f"Iteration {iteration} consolidated: {enhanced_query}", 
                        iteration_results
                    )
                    
                    # Add to our collection of understandings
                    intermediate_understandings.append({
                        "iteration": iteration,
                        "query": enhanced_query,
                        "understanding": consolidated_understanding,
                        "type": "consolidated"
                    })
                    
                    print(f"\n=== Consolidated Understanding for Iteration {iteration} ===")
                    print(consolidated_understanding)
                    print("==========================================================")
                
                # Update results for the next iteration
                results = iteration_results
            
            # Generate final comprehensive answer with follow-up questions
            print("\nGenerating comprehensive answer based on all search results and intermediate understandings...")
            final_result = engine.generate_final_answer(enhanced_query, all_results, intermediate_understandings)
            
            print("\n=== Final Comprehensive Answer ===")
            print(final_result["answer"])
            print("==================================")
            
            print("\n=== Follow-up Questions ===")
            for i, question in enumerate(final_result["follow_up_questions"]):
                print(f"{i+1}. {question}")
            print("==========================")
            
            # Ask if user wants to explore a follow-up question
            explore_followup = input("\nWould you like to explore one of these follow-up questions? (1-3, or n): ")
            if explore_followup.lower() not in ('n', 'no'):
                try:
                    question_index = int(explore_followup) - 1
                    if 0 <= question_index < len(final_result["follow_up_questions"]):
                        # Start a new search with the selected follow-up question
                        query = final_result["follow_up_questions"][question_index]
                        print(f"\nStarting new search for: {query}")
                        continue  # This will restart the while loop with the new query
                except ValueError:
                    pass  # Invalid input, continue with saving
            
            # Option to save the results
            save_results = input("\nWould you like to save these results? (y/n): ")
            if save_results.lower() == 'y':
                filepath = engine.save_results_with_html(enhanced_query, max_iterations, final_result, all_results, intermediate_understandings)
                if filepath:
                    print(f"Results saved to {filepath}")
                    
                    # Check if HTML file was generated
                    html_filepath = os.path.splitext(filepath)[0] + '.html'
                    if os.path.exists(html_filepath):
                        print(f"HTML presentation available at: {html_filepath}")
                        
                        # Try to open the HTML file in the default browser
                        try:
                            import webbrowser
                            webbrowser.open('file://' + os.path.abspath(html_filepath))
                            print("Opening HTML presentation in your browser...")
                        except:
                            pass
    finally:
        # Make sure we close the browser properly
        print("Cleaning up resources...")
        engine.cleanup()