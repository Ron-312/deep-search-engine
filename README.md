# Deep Search Engine

A sophisticated search solution that leverages Large Language Models to provide detailed, well-cited answers to complex queries. This engine goes beyond traditional search by synthesizing information from multiple sources into comprehensive, structured responses.

---

## Features

- **Multi-iteration Intelligence**: Automatically generates follow-up queries to build a deeper understanding of your topic
- **Human-like Content Extraction**: Scrapes detailed content from web pages with natural browsing patterns to avoid detection
- **LLM-Powered Synthesis**: Uses local LLM models via LM Studio to synthesize information from multiple sources
- **Source Attribution**: Includes proper citations for all information in generated answers
- **Interactive Interface**: Simple command-line interface for complex search operations
- **Beautiful HTML Reports**: Generates responsive HTML presentations of search results for easy sharing
- **Concurrent Processing**: Parallel content fetching and query processing for faster results
- **JSON Schema Support**: Structured output using JSON schemas for reliable response parsing

---

## Project Structure

### Key Components

#### `SearchEngine` (src/search/engine.py)
The core component that orchestrates the search process:
- Enhances search queries for better results
- Manages search result retrieval
- Coordinates content fetching
- Generates intermediate and final answers

#### `LmStudioClient` (src/llm/lm_studio_client.py)
Provides integration with LM Studio's local API:
- Enhances search queries
- Generates follow-up questions
- Synthesizes information into coherent answers
- Supports JSON schema for structured outputs

#### `GoogleScraperPlaywright` (src/web_scraper/google_scraper.py)
Advanced web scraper with human-like behavior:
- Performs Google searches with natural timing
- Extracts search results avoiding detection
- Fetches full content from result pages
- Supports concurrent browsing for faster results

#### `HTML Generator` (src/utils/html_generator.py)
Creates beautiful HTML presentations of search results:
- Responsive design for all devices
- Proper formatting of Markdown content
- Clickable source links
- Follow-up questions section
- Index page for browsing past searches

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/deep-search-engine.git
cd deep-search-engine
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Browser for Playwright
```bash
playwright install
```

### 4. Setup LM Studio
- Download and install [LM Studio](https://lmstudio.ai/)
- Launch LM Studio and download a suitable model (e.g., Mistral-7B, Llama-2)
- Start the local server in LM Studio on the default port (1234)

### 5. Configure Settings
Edit `settings.yml` as needed:
- Set preferred search parameters
- Set model configurations (temperature, max tokens, etc.)

---

## Usage

### Basic Usage
This launches the interactive search interface:
```bash
python main.py
```
- Enter natural language search queries
- Specify the number of search iterations (1-3 recommended)
- View intermediate search understandings
- Save comprehensive answers as JSON and HTML reports

### Example Queries
The engine excels at complex, research-oriented queries:
- "What are the latest developments in quantum computing?"
- "Compare different approaches to sustainable urban planning"
- "Find me a place to stay in Berlin with good public transport access"
- "Explain the impact of artificial intelligence on healthcare diagnostics"

---

## Advanced Usage

### Saving and Viewing Results
After completing a search, you can save the results:
- JSON output for structured data
- HTML output for readable, shareable reports

### Concurrent Content Fetching
- By default: fetches from 3 websites concurrently
- Adjust in the code: `concurrent_fetch_limit`

### Performance Optimization
- **Concurrent Browsing**: 2-3 concurrent browser instances recommended
- **Iteration Count**: 2 iterations offer good depth, 3 for complex topics
- **LLM Temperature**: ~0.7 balances creativity and factual accuracy
- **HTML Generation**: Done in background to avoid blocking

---

## Troubleshooting

- **Browser Initialization Issues**: Restart the app or re-run `playwright install`
- **JSON Parsing Errors**: Retry logic is built-in for malformed responses
- **Rate Limiting**: Lower the search frequency or increase timeouts

---

## Contributing

Contributions are welcome! Please submit a Pull Request:
```bash
git checkout -b feature/amazing-feature
git commit -m 'Add some amazing feature'
git push origin feature/amazing-feature
```
Then open a Pull Request from your fork.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for web automation
- Uses [LM Studio](https://lmstudio.ai/) for local LLM inference
- Inspired by Retrieval-Augmented Generation (RAG) techniques