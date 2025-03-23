import json
import os
import re
import markdown
import datetime
from pathlib import Path

def generate_html_from_result(result_file_path):
    """
    Generate an HTML presentation page from a search result JSON file.
    
    Args:
        result_file_path: Path to the JSON result file
        
    Returns:
        Path to the generated HTML file
    """
    try:
        # Load the JSON data
        with open(result_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract key information
        query = data.get('query', 'Unknown query')
        answer = data.get('answer', 'No answer available')
        follow_up_questions = data.get('follow_up_questions', [])
        sources = data.get('sources', [])
        intermediate_understandings = data.get('intermediate_understandings', [])
        
        # Convert the answer from Markdown to HTML
        answer_html = markdown.markdown(answer, extensions=['extra', 'codehilite'])
        
        # Fix sources to have proper links
        for i, source in enumerate(sources):
            if 'url' in source and source['url']:
                source_text = source.get('title', f'Source {i+1}')
                answer_html = answer_html.replace(f'[Source {i+1}]', f'<a href="{source["url"]}" target="_blank" class="source-link">[Source {i+1}]</a>')
        
        # Generate HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results: {query}</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #3b82f6;
            --background-color: #f8fafc;
            --text-color: #334155;
            --heading-color: #1e3a8a;
            --border-color: #e2e8f0;
            --source-color: #059669;
            --blockquote-bg: #f1f5f9;
            --code-bg: #f1f5f9;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        header {{
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: var(--heading-color);
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 2rem;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }}
        
        h2 {{
            font-size: 1.75rem;
        }}
        
        h3 {{
            font-size: 1.5rem;
        }}
        
        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .source-link {{
            color: var(--source-color);
            font-weight: 500;
            text-decoration: none;
        }}
        
        .query-box {{
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1.5rem;
        }}
        
        .answer-container {{
            padding: 1rem 0;
        }}
        
        .followup-section {{
            background-color: var(--blockquote-bg);
            padding: 1.5rem;
            border-radius: 4px;
            margin-top: 2rem;
        }}
        
        .followup-section h3 {{
            margin-top: 0;
        }}
        
        .followup-questions {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .followup-questions li {{
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .followup-questions li:last-child {{
            border-bottom: none;
        }}
        
        .sources-section {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
        }}
        
        .sources-list {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .sources-list li {{
            padding: 0.5rem 0;
        }}
        
        code {{
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
            font-size: 0.9rem;
        }}
        
        pre {{
            background-color: var(--code-bg);
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
        }}
        
        blockquote {{
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin-left: 0;
            color: #4b5563;
            background-color: var(--blockquote-bg);
            padding: 0.5rem 1rem;
            border-radius: 0 4px 4px 0;
        }}
        
        .footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.9rem;
            color: #64748b;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .container {{
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Deep Search Results</h1>
        <div class="query-box">
            <strong>Query:</strong> {query}
        </div>
    </header>
    
    <main class="container">
        <div class="answer-container">
            {answer_html}
        </div>
        
        <div class="followup-section">
            <h3>Follow-up Questions</h3>
            <ul class="followup-questions">
                {"".join([f'<li><a href="#">{q}</a></li>' for q in follow_up_questions])}
            </ul>
        </div>
        
        <div class="sources-section">
            <h3>Sources</h3>
            <ul class="sources-list">
                {"".join([f'<li><a href="{s.get("url", "#")}" target="_blank">{s.get("title", f"Source {i+1}")}</a></li>' for i, s in enumerate(sources)])}
            </ul>
        </div>
    </main>
    
    <footer class="footer">
        <p>Generated by Deep Search Engine on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>
"""
        
        # Write HTML to file
        html_file_path = os.path.splitext(result_file_path)[0] + '.html'
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"HTML presentation generated at: {html_file_path}")
        return html_file_path
    
    except Exception as e:
        print(f"Error generating HTML: {e}")
        return None

def generate_html_for_results_directory(results_dir):
    """
    Generate HTML presentations for all JSON files in the results directory.
    
    Args:
        results_dir: Path to the results directory
        
    Returns:
        List of paths to generated HTML files
    """
    html_files = []
    
    # Ensure the directory exists
    if not os.path.exists(results_dir):
        print(f"Results directory not found: {results_dir}")
        return html_files
    
    # Process all JSON files
    for file in os.listdir(results_dir):
        if file.endswith('.json'):
            file_path = os.path.join(results_dir, file)
            html_file = generate_html_from_result(file_path)
            if html_file:
                html_files.append(html_file)
    
    return html_files

def generate_index_page(results_dir, html_files):
    """
    Generate an index page that lists all search result HTML files.
    
    Args:
        results_dir: Path to the results directory
        html_files: List of HTML file paths
        
    Returns:
        Path to the generated index HTML file
    """
    # Sort files by modification time (newest first)
    sorted_files = sorted(html_files, key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Extract query and date info for each file
    file_info = []
    for file_path in sorted_files:
        try:
            # Get modification time
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Extract query from file name or content
            query = "Unknown query"
            try:
                # Try to get the query from the corresponding JSON file
                json_path = os.path.splitext(file_path)[0] + '.json'
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        query = data.get('query', "Unknown query")
            except:
                # If that fails, use a generic name
                base_name = os.path.basename(file_path)
                query = f"Search {base_name}"
            
            file_info.append({
                'path': file_path,
                'query': query,
                'date': mod_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        except:
            continue
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Search Engine - Results Index</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #3b82f6;
            --background-color: #f8fafc;
            --text-color: #334155;
            --heading-color: #1e3a8a;
            --border-color: #e2e8f0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 2rem;
        }}
        
        header {{
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        h1 {{
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }}
        
        .search-list {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .search-list li {{
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .search-list li:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .search-list a {{
            text-decoration: none;
            color: var(--primary-color);
            font-weight: 500;
            font-size: 1.1rem;
            display: block;
        }}
        
        .search-date {{
            font-size: 0.9rem;
            color: #64748b;
            margin-top: 0.5rem;
        }}
        
        .footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.9rem;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Deep Search Engine</h1>
        <p>Index of search results</p>
    </header>
    
    <main class="container">
        <ul class="search-list">
            {"".join([f'<li><a href="{os.path.basename(info["path"])}">{info["query"]}</a><div class="search-date">{info["date"]}</div></li>' for info in file_info])}
        </ul>
    </main>
    
    <footer class="footer">
        <p>Generated by Deep Search Engine on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>
"""
    
    # Write HTML to file
    index_path = os.path.join(results_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Index page generated at: {index_path}")
    return index_path

if __name__ == "__main__":
    # This allows the script to be run directly
    import sys
    
    if len(sys.argv) > 1:
        # Process a specific file
        file_path = sys.argv[1]
        if os.path.isfile(file_path) and file_path.endswith('.json'):
            generate_html_from_result(file_path)
        elif os.path.isdir(file_path):
            html_files = generate_html_for_results_directory(file_path)
            if html_files:
                generate_index_page(file_path, html_files)
    else:
        # Default to results directory
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'results')
        html_files = generate_html_for_results_directory(results_dir)
        if html_files:
            generate_index_page(results_dir, html_files)