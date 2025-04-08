import requests
import json
import re
import os
import traceback
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

class LmStudioClient:
    def __init__(self, api_base=None, backend="lm_studio"):
        """
        Initialize the client with support for both LM Studio and OpenAI.
        
        Args:
            api_base: Base URL for LM Studio API (defaults to value from .env)
            backend: Either "lm_studio" or "openai" (default: "lm_studio")
        """
        # Load from environment if not provided
        self.lm_studio_api_base = api_base or os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        # Set default backend
        self.set_backend(backend)
        self.model_name = None
        self.openai_model = "gpt-4o-mini"  # Default OpenAI model
        
    def set_backend(self, backend, method_overrides=None):
        """
        Set the backend to use for generating responses.
        
        Args:
            backend: Either "lm_studio" or "openai"
            method_overrides: Optional dict of methods that should use a specific backend
                             regardless of the default setting (e.g. {"generate_page_understanding": "openai"})
        """
        if backend not in ["lm_studio", "openai"]:
            raise ValueError("Backend must be either 'lm_studio' or 'openai'")
            
        if backend == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI backend selected but no API key provided. Add OPENAI_API_KEY to your .env file.")
            
        self.backend = backend
        self.method_overrides = method_overrides or {}
        
    def set_model(self, model_name, backend=None):
        """
        Set the model to use for the specified backend.
        
        Args:
            model_name: The model name to use
            backend: Which backend this model applies to (if None, uses current default backend)
        """
        if backend is None:
            backend = self.backend
            
        if backend == "lm_studio":
            self.model_name = model_name
        elif backend == "openai":
            self.openai_model = model_name
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _get_backend_for_method(self, method_name):
        """
        Determine which backend to use for a given method based on overrides.
        
        Args:
            method_name: Name of the method being called
            
        Returns:
            Either "lm_studio" or "openai"
        """
        return self.method_overrides.get(method_name, self.backend)
    
    def generate_response(self, prompt, temperature=0.7, max_tokens=1024, schema=None, method_name=None, backend=None):
        """
        Generate a response using either LM Studio or OpenAI based on current backend.
        
        Args:
            prompt: The user's input text
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            schema: Optional JSON schema to enforce structured output
            method_name: Name of the calling method for backend selection
            backend: Explicitly override backend for this specific request ("lm_studio" or "openai")
            
        Returns:
            The generated text response, formatted according to schema if provided
        """
        # Determine which backend to use with priority:
        # 1. Explicit backend parameter
        # 2. Method override
        # 3. Default backend
        if backend and backend in ["lm_studio", "openai"]:
            use_backend = backend
        elif method_name and method_name in self.method_overrides:
            use_backend = self.method_overrides[method_name]
        else:
            use_backend = self.backend
            
        # Call appropriate implementation
        if use_backend == "lm_studio":
            return self._generate_response_lm_studio(prompt, temperature, max_tokens, schema)
        elif use_backend == "openai":
            return self._generate_response_openai(prompt, temperature, max_tokens, schema)
        else:
            raise ValueError(f"Unknown backend: {use_backend}")
    
    def _generate_response_lm_studio(self, prompt, temperature=0.7, max_tokens=1024, schema=None):
        """LM Studio implementation of generate_response"""
        if self.model_name is None:
            raise ValueError("Model not set. Please set a model using set_model().")
        
        url = f"{self.lm_studio_api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add response_format with schema if provided
        if schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_structure",
                    "schema": schema
                }
            }
        
        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            # Extract the content from the response
            content = result["choices"][0]["message"]["content"]
            # Remove any <think>...</think> sections, including the tags
            cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            # If schema was provided, handle JSON
            if schema:
                # Check if the content is enclosed in a JSON code block
                match = re.search(r'```json\s*(.*?)\s*```', cleaned_content, flags=re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                else:
                    json_str = cleaned_content.strip()
                
                try:
                    parsed_json = json.loads(json_str)
                    return parsed_json
                except json.JSONDecodeError as e:
                    print(f"Warning: Response did not contain valid JSON despite schema: {e}")
                    # Fall back to returning the raw string if parsing fails
                    return json_str
        
            # Regular content processing (no schema or fallback)
            # Check if the cleaned content is enclosed in a JSON code block
            match = re.search(r'```json\s*(.*?)\s*```', cleaned_content, flags=re.DOTALL)
            if match:
                cleaned_content = match.group(1)
            
            # Return the cleaned content with any leading/trailing whitespace removed
            return cleaned_content.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LM Studio API: {e}")
            return f"Error: {str(e)}"
    
    def _generate_response_openai(self, prompt, temperature=0.7, max_tokens=1024, schema=None):
        """OpenAI implementation of generate_response using function calling with provided schema"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check your API key.")
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            if schema:
                # Use the provided schema directly as function parameters
                function_name = "generate_structured_response"
                
                # Define the tool/function using the exact schema provided
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "description": "Generate a structured response based on the user query",
                            "parameters": schema  # Use the schema exactly as provided
                        }
                    }
                ]
                
                # Call OpenAI API with function calling
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": function_name}},
                    temperature=temperature,
                    max_tokens=max_tokens,  
                    response_format={ "type": "json_object" }
                )
                
                # Extract the function call arguments
                tool_call = response.choices[0].message.tool_calls[0]
                function_args = json.loads(tool_call.function.arguments)
                
                return function_args
            else:
                # For regular text responses without schema
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Extract content from response
                content = response.choices[0].message.content
                return content
                
        except Exception as e:
            print(f"Error generating response with OpenAI: {e}")
            print(f"Exception details: {str(e)}")
            traceback.print_exc()
            return f"Error: {str(e)}"

    def generate_search_query(self, user_query):
        """
        Generate an optimized search query for Google based on the user's original query.
        
        Args:
            user_query: The original user question/query
            
        Returns:
            A search query optimized for Google
        """
        if self.model_name is None:
            raise ValueError("Model not set. Please set a model using set_model().")
        
        prompt = f"""You are an expert at formulating Google search queries. 
    Given a user question, generate the best search query to find relevant information.
    Focus on key concepts and use search operators when helpful.

    Format your response as a JSON object with a single field:
    {{
    "search_query": "Your optimized search query here"
    }}

    User question: {user_query}

    Return ONLY the JSON object without any additional text or explanations:"""

        try:
            response_text = self.generate_response(prompt)      
            # Remove any markdown code block markers if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse the JSON string into a Python dictionary
            json_obj = json.loads(response_text)
            
            # Handle different response formats
            if isinstance(json_obj, list):
                # If we got a list, check if any item has search_query
                for item in json_obj:
                    if isinstance(item, dict) and 'search_query' in item:
                        return item['search_query']
                # If no search_query found, return first string item or original query
                for item in json_obj:
                    if isinstance(item, str):
                        return item
                return user_query
            else:
                # Return only the search query value; fallback to original query if key not found
                return json_obj.get("search_query", user_query)
        except Exception as e:
            print(f"Error generating search query: {e}")
            return user_query  # Fallback to original query
        
    # def generate_response(self, prompt, temperature=0.7, max_tokens=1024, schema=None):
    #     """
    #     Generate a response using the LM Studio local API.
        
    #     Args:
    #         prompt: The user's input text
    #         temperature: Controls randomness (0.0 to 1.0)
    #         max_tokens: Maximum number of tokens to generate
    #         schema: Optional JSON schema to enforce structured output
            
    #     Returns:
    #         The generated text response, formatted according to schema if provided
    #     """
    #     if self.model_name is None:
    #         raise ValueError("Model not set. Please set a model using set_model().")
        
    #     url = f"{self.api_base}/chat/completions"
        
    #     payload = {
    #         "model": self.model_name,
    #         "messages": [
    #             {"role": "user", "content": prompt}
    #         ],
    #         "temperature": temperature,
    #         "max_tokens": max_tokens
    #     }
        
    #     # Add response_format with schema if provided (CORRECTED FORMAT)
    #     if schema:
    #         payload["response_format"] = {
    #             "type": "json_schema",
    #             "json_schema": {
    #                 "name": "response_structure",  # Add a name for the schema
    #                 "schema": schema  # Your actual schema definition goes here
    #             }
    #         }
        
    #     headers = {
    #         "Content-Type": "application/json"
    #     }
    #     try:
    #         response = requests.post(url, headers=headers, data=json.dumps(payload))
    #         response.raise_for_status()  # Raise exception for HTTP errors
            
    #         result = response.json()
    #         # Extract the content from the response
    #         content = result["choices"][0]["message"]["content"]
    #         # Remove any <think>...</think> sections, including the tags
    #         cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
    #         # If schema was provided, handle JSON
    #         if schema:
    #             # Check if the content is enclosed in a JSON code block
    #             match = re.search(r'```json\s*(.*?)\s*```', cleaned_content, flags=re.DOTALL)
    #             if match:
    #                 json_str = match.group(1).strip()
    #             else:
    #                 json_str = cleaned_content.strip()
                
    #             # If requested, return the raw JSON string for debugging
    #             # if return_raw_json:
    #             #     return json_str
                    
    #             # Otherwise parse the JSON as before
    #             try:
    #                 parsed_json = json.loads(json_str)
    #                 return parsed_json
    #             except json.JSONDecodeError as e:
    #                 print(f"Warning: Response did not contain valid JSON despite schema: {e}")
    #                 # Fall back to returning the raw string if parsing fails
    #                 return json_str
        
    #         # Regular content processing (no schema or fallback)
    #         # Check if the cleaned content is enclosed in a JSON code block
    #         match = re.search(r'```json\s*(.*?)\s*```', cleaned_content, flags=re.DOTALL)
    #         if match:
    #             cleaned_content = match.group(1)
            
    #         # Return the cleaned content with any leading/trailing whitespace removed
    #         return cleaned_content.strip()
    #     except requests.exceptions.RequestException as e:
    #         print(f"Error communicating with LM Studio API: {e}")
    #         return f"Error: {str(e)}"
            
    def chat_completion(self, messages, temperature=0.7, max_tokens=1024):
        """
        More flexible method that accepts a full messages array for multi-turn conversation.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The complete API response
        """
        if self.model_name is None:
            raise ValueError("Model not set. Please set a model using set_model().")
        
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LM Studio API: {e}")
            return {"error": str(e)}
            
    def generate_answer(self, query, search_results, is_final=False):
        """Generate an answer using the LLM based on search results."""
        if not search_results:
            return "I couldn't find any relevant information to answer your question."
        
        # Sort results by relevance score from highest to lowest
        sorted_results = sorted(
            [r for r in search_results if r.get('url') and r.get('page_analysis')],
            key=lambda x: x.get('page_analysis', {}).get('relevance_score', 0),
            reverse=True
        )
        
        # Create context from the top 7 highest-scored search results
        context_list = []
        for result in sorted_results[:7]:  # Take top 7 instead of 3
            # Get page analysis data
            page_analysis = result.get('page_analysis', {})
            summary = page_analysis.get('summary', '')
            relevance_score = page_analysis.get('relevance_score', 0)
            
            # Fallback to snippet if no analysis available
            if not summary:
                summary = result.get('snippet', '')
            
            # Build context string with title, URL, relevance score and full summary
            context_list.append(
                f"Title: {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Relevance Score: {relevance_score}/10\n"
                f"Summary: {summary}"  # Use full summary without truncation
            )
        
        # Join all context pieces with double newlines for readability
        context = "\n\n".join(context_list)
        
        
        # Different prompt based on whether this is the final answer or an intermediate step.
        if is_final:
            prompt = f"""Based on all the following web search results, please provide a comprehensive answer to the query: "{query}"
            
    Search Results:
    {context}

    In your answer, please:
    - Provide a detailed explanation of the topic, incorporating insights from the search results.
    - Break down your explanation into bullet points, with each bullet covering a specific aspect of the subject.
    - Elaborate on the thought process used to synthesize the information, describing what was learned from each source.
    - Explain key concepts, trends, and any connections you have identified.
    - Ensure that your response is at least 300 words long.
    - Conclude your answer with a final bullet point summarizing your overall findings and understanding.

    Format your response as a JSON object with a single field:
    {{
    "thinking": "Your analysis process and reasoning behind the answer",
    "answer": "Your detailed, comprehensive answer that synthesizes information from multiple sources here..."
    }}

    Return ONLY the JSON object and nothing else."""
        else:
            prompt = f"""Based on the following web search results, please answer the query: "{query}"
            
    Search Results:
    {context}

    In your answer, please:
    - Provide a detailed explanation based on the current available information.
    - Outline the key points in bullet format.
    - Briefly describe the thought process behind your answer.
    - Keep your response succinct while ensuring clarity.

    Format your response as a JSON object with a single field:
    {{
    "thinking": "Your analysis process and reasoning behind the answer",
    "answer": "Your concise intermediate answer based on the current information here..."
    }}

    Return ONLY the JSON object and nothing else."""
        
        # Define schema for structured answer output
        answer_schema = {
            "type": "object",
            "properties": {
                "thinking": {
                    "type": "string", 
                    "description": "Your analysis process and reasoning behind the answer"
                },
                "answer": {
                    "type": "string", 
                    "description": "Your detailed response to the query based on the search results"
                }
            },
            "required": ["thinking", "answer"]
        }
        
        # Generate response using the prompt with schema
        response_json = self.generate_response(prompt, schema=answer_schema, backend="openai")
        
        
        # # Remove any markdown code block markers if present
        # if response_text.startswith("```json"):
        #     response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # # Parse the JSON string into a Python dictionary
        # json_obj = json.loads(response_text)
        
        # Return only the answer value; fallback to original query if key not found
        return response_json.get("answer", response_json)
    
    def generate_follow_up_queries(self, original_query, current_results, max_queries=2):
        """Generate follow-up search queries based on the original query and current results."""
        
        # Create context from current results
        context = "\n\n".join([
            f"Title: {result.get('title', 'No title')}\nURL: {result.get('url', 'No URL')}\nSnippet: {result.get('snippet', '')[:300]}..."
            for result in current_results[:3] if result.get('url')
        ])
        
        prompt = f"""Original Question: "{original_query}"

        I've already searched for information and found these results:
        {context}

        Based on these results, what {max_queries} additional search queries should I make to get more comprehensive information?
        Focus on different aspects of the original question or follow up on interesting leads in the current results.
        The goal is to build a more complete understanding of the topic through multiple searches. don't be afraid to get creative! we need to cover a wide range of relevant information.

        Format your response as a JSON object with a single field "queries" containing an array of exactly {max_queries} search queries:

        Example format:
        {{
        "queries": [
            "First follow-up search query",
            "Second follow-up search query"
        ]
        }}

        Ensure you return ONLY the JSON object without any additional text, formatting, or explanation."""

        try:
            response_text = self.generate_response(prompt)
            parsed_response = json.loads(response_text)
            
            # Extract queries from the JSON object directly
            if "queries" in parsed_response and isinstance(parsed_response["queries"], list):
                queries = parsed_response["queries"]
                
                # Ensure we have the requested number of queries
                while len(queries) < max_queries and len(queries) > 0:
                    queries.append(queries[0])  # Duplicate the first query if needed
                    
                return queries[:max_queries]
        except Exception as e:
            print(f"Error generating follow-up queries: {e}")
            # Fallback to simple variations
            return [f"{original_query} explained", f"{original_query} details"]

    def get_query_clarification(self, query):
        """
        Analyze the initial query and generate clarifying questions if needed.
        
        Args:
            query: The user's initial query
            
        Returns:
            A dictionary with 'needs_clarification' (boolean) and 'questions' (list)
        """
        prompt = f"""Analyze this user query: "{query}"
                
        Determine if you need any clarification before searching for an answer. If the query is ambiguous, 
        vague, or could be interpreted in multiple ways, generate 1-3 specific clarifying questions.
        If the query is clear and specific enough to search effectively, don't ask any questions.

        Format your response as a JSON object with two fields:
        1. "needs_clarification": true/false - whether clarification is needed
        2. "questions": an array of 0-3 clarifying questions (empty if needs_clarification is false)
        3. "explanation": a brief explanation of why clarification is or isn't needed

        Example format for unclear query:
        {{
        "needs_clarification": true,
        "questions": [
            "What specific aspect of X are you interested in?",
            "Are you looking for information about X in any particular context or time period?"
        ],
        "explanation": "The query is quite broad and could be interpreted in several ways."
        }}

        Example format for clear query:
        {{
        "needs_clarification": false,
        "questions": [],
        "explanation": "The query is specific and clear enough to search effectively."
        }}

        Return ONLY the JSON object and nothing else."""

        try:
            response = self.generate_response(prompt)
            
            # Try to parse as JSON
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # If parsing fails, use a simple fallback
                print("Error parsing clarification response as JSON")
                return {
                    "needs_clarification": False,
                    "questions": []
                }
        except Exception as e:
            print(f"Error generating clarification questions: {e}")
            return {
                "needs_clarification": False,
                "questions": []
            }

            
    def generate_markdown_outline(self, query, search_results, intermediate_understandings=None):
        """
        Stage 1: Generate a Markdown outline for the final answer with source allocations.
        
        Expected JSON format:
        {
        "outline": "## Section 1\\n- bullet\\n## Section 2\\n- bullet...",
        "section_sources": {
            "## Section 1": [1, 3, 5],
            "## Section 2": [2, 4, 7]
        }
        }
        """
        if not search_results:
            return "I couldn't find any relevant information to answer your question."
        
        # Sort results by relevance score from highest to lowest
        sorted_results = sorted(
            [r for r in search_results if r.get('url') and r.get('page_analysis')],
            key=lambda x: x.get('page_analysis', {}).get('relevance_score', 0),
            reverse=True
        )
        
        # Create context from the top 7 highest-scored search results
        context_list = []
        for idx, result in enumerate(sorted_results[:7]):  # Take top 7 instead of 3
            # Get page analysis data
            page_analysis = result.get('page_analysis', {})
            summary = page_analysis.get('summary', '')
            relevance_score = page_analysis.get('relevance_score', 0)
            
            # Add source ID to make it clear in the prompt
            source_id = idx + 1
            
            # Fallback to snippet if no analysis available
            if not summary:
                summary = result.get('snippet', '')
            
            # Build context string with source ID, title, URL, relevance score and full summary
            context_list.append(
                f"SOURCE {source_id}:\n"
                f"Title: {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Relevance Score: {relevance_score}/10\n"
                f"Summary: {summary}"  # Use full summary without truncation
            )
        
        # Join all context pieces with double newlines for readability
        context = "\n\n".join(context_list)
        
        # Combine intermediate understandings if available
        if intermediate_understandings:
            understandings_str = "\n\n".join([
                f"Iteration {item.get('iteration', '?')} - Understanding: {item.get('understanding', 'Unknown')}"
                for item in intermediate_understandings
            ])
        else:
            understandings_str = "None"

        # Enhanced prompt that instructs the LLM to return a JSON object with both outline and source allocations
        prompt = f"""
        You have the following query: "{query}"
        You have these search results:
        {context}

        You also have these intermediate understandings:
        {understandings_str}

        Create a well-structured outline in Markdown for answering this query.

        FORMATTING INSTRUCTIONS:
        1. Use ## for main sections and ### for subsections
        2. Format bullet points with proper indentation:
        - First level bullets should start with a single dash
        - Second level bullets should be indented with two spaces
        3. DO NOT include source citations like [1,2,3] within the outline text
        4. Each section should have a descriptive header
        5. Structure should be clean with consistent formatting throughout
        6. IMPORTANT: Assign AT MOST 3 SOURCES to each section - be selective and choose only the most relevant sources
        7. Not every source needs to be used - prioritize quality over quantity

        Return a JSON object with the following fields:
        1. "outline": Your markdown outline with proper hierarchy
        2. "section_sources": An object mapping section headers to source IDs

        Example format:
        {{
        "outline": "## Introduction\\n- Overview of the topic\\n- Key concepts\\n\\n### Historical Context\\n- Historical development\\n\\n## Main Points\\n- First important aspect\\n  - Supporting details\\n\\n### Key Considerations\\n- Critical factors\\n- Important elements\\n\\n## Specific Examples\\n- Case study one\\n- Case study two\\n\\n## Analysis\\n- Interpretation of findings\\n- Implications\\n\\n## Conclusion\\n- Summary of key points\\n- Final thoughts",
        "section_sources": {{
            "## Introduction": [1, 3],
            "### Historical Context": [2],
            "## Main Points": [4, 5, 7],
            "### Key Considerations": [3, 6],
            "## Specific Examples": [2, 7],
            "## Analysis": [1, 4],
            "## Conclusion": [5]
        }}
        }}
        """
        # Enhanced schema that enforces proper structure
        outline_schema = {
            "type": "object",
            "properties": {
                "thinking": {
                    "type": "string", 
                    "description": "Here you can explain your thought process, considerations, or challenges faced while creating the outline"
                },
                "outline": {
                    "type": "string", 
                    "description": "Complete hierarchical markdown outline with ## for main sections and ### for subsections"
                },
                "section_sources": {
                    "type": "object",
                    "description": "Mapping of section headers (including ### subsections) to relevant source IDs",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of source IDs (integers) relevant to this section"
                    }
                }
            },
            "required": ["thinking", "outline", "section_sources"]
        }

        try:
            response = self.generate_response(prompt, schema=outline_schema, temperature=0.5, backend="openai")
            
            
            # If we received a dictionary directly, return it
            if isinstance(response, dict) and "outline" in response and "section_sources" in response:
                return response
                
            # Otherwise, try to parse the response as JSON
            try:
                # Remove any markdown code fence markers
                if isinstance(response, str):
                    if response.startswith("```json"):
                        response = response.replace("```json", "").replace("```", "").strip()
        
                    # Parse the JSON
                    json_obj = json.loads(response)
                    
                    # Validate the response has required fields
                    if "outline" not in json_obj or "section_sources" not in json_obj:
                        raise ValueError("Invalid response structure, missing required fields")
                    
                    return json_obj
                else:
                    raise ValueError("Response is neither a valid JSON string nor a dictionary")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse JSON response in generate_markdown_outline: {e}")
                # Return a default structure with just the outline
                return {
                    "outline": response if isinstance(response, str) else "Error: Could not parse the outline as JSON.",
                    "section_sources": {}
                }
                
        except Exception as e:
            print(f"Error communicating with generate_markdown_outline: {e}")
            return {
                "outline": "Error: Exception in generate_markdown_outline.",
                "section_sources": {}
            }

    def expand_markdown_section(self, query, all_sections_so_far, section_header):
        """
        Stage 2: Expand one section of the answer at a time in Markdown format, returned as JSON.
        
        Expected JSON format:
        {
          "section_text": "# The expanded markdown content for this section..."
        }
        """
        prompt = f"""
We have an ongoing answer for the query: "{query}" in Markdown format.
So far, the collected sections are:

{all_sections_so_far}

Now we want to fill out this section in detail:
"{section_header}"

Write the content for this section in Markdown. Be detailed, use bullet points or subheadings if needed,
and make sure it flows logically from the sections that came before it.

Return ONLY a JSON object in the following format:
{{
  "section_text": "Your Markdown for this specific section"
}}
"""

        try:
            response_text = self.generate_response(prompt, backend="openai")
            try:
                # Remove code fence markers
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()

                # Parse into JSON
                json_obj = json.loads(response_text)
                
                # Validate structure
                section_text = json_obj.get("section_text", "")
                if not isinstance(section_text, str):
                    raise ValueError("Invalid or missing 'section_text' field in JSON response")

                return section_text
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse JSON response in expand_markdown_section: {e}")
                return f"# Error: Could not parse the JSON for section: {section_header}"
        except Exception as e:
            print(f"Error in expand_markdown_section: {e}")
            return "# Error: Exception in expand_markdown_section."

    def _build_result_id_mapping(self, search_results):
        """
        Create a mapping from sequential source IDs to original result IDs
        """
        # Create mapping from sequential source IDs (1, 2, 3...) to original result IDs
        source_id_map = {}
        for idx, result in enumerate(search_results):
            if 'url' in result and result['url']:
                source_id = idx + 1  # Sequential ID (1-based)
                original_id = result.get('id')  # Original result ID
                source_id_map[source_id] = original_id
        
        return source_id_map

    def generate_answer_in_multiple_stages(self, query, search_results, intermediate_understandings=None):
        """
        Controller function that orchestrates a multi-stage answer generation process:
        1) Generates a structured Markdown outline
        2) Expands each section of the outline sequentially, with context awareness
        3) Adds citations and source attribution throughout the answer
        4) Generates follow-up questions based on the complete answer
        5) Returns a complete, well-structured response with citations and follow-ups
        
        Args:
            query: The user's original query
            search_results: List of search result dictionaries
            intermediate_understandings: Optional list of intermediate understanding dictionaries
            
        Returns:
            Dictionary with "answer" (Markdown string) and "follow_up_questions" (list)
        """        
        print("Stage 1: Generating structured outline...")
        
        # Step 1: Build an evidence base with key information from results
        evidence_base = self._build_evidence_base(search_results)
        
        # Step 1.5: Create source ID mapping
        source_id_map = self._build_result_id_mapping(search_results)
    
        
        # Step 2: Get the Markdown outline
        outline_result = self.generate_markdown_outline(query, search_results, intermediate_understandings)
        outline_markdown = outline_result.get("outline", "")
        section_to_sources = outline_result.get("section_sources", {})
    
        # Step 3: Parse the outline into sections more robustly
        hierarchical_sections = self._parse_markdown_outline(outline_markdown)
        
        # Flatten the hierarchical structure to process all sections and subsections
        sections = self._flatten_sections(hierarchical_sections)
        
        if not sections:
            print("Warning: Could not parse outline into sections. Using default structure.")
            sections = [
            {'header': '## Introduction', 'content': []},
            {'header': '## Main Discussion', 'content': []},
            {'header': '## Conclusion', 'content': []}
            ]
        
        print(f"Parsed outline into {len(sections)} sections and subsections")
        
        # Step 4: Expand each section with the LLM, tracking sources
        print("Stage 2: Expanding sections sequentially...")
        final_markdown_sections = []
        section_sources = {}  # Track which sources were used in each section
        
        for idx, section in enumerate(sections):
            print(f"Expanding section {idx+1}/{len(sections)}: {section['header']}")
            
            # Build context of all expanded sections so far
            text_so_far = "\n\n".join(final_markdown_sections)
            section_header = section['header']
            
            # Include the content bullets from the outline in the section header
            section_content_points = ""
            if section.get('content') and len(section['content']) > 0:
                section_content_points = "\nOutline points:\n" + "\n".join(section['content'])
            
            # Get the sequential source IDs allocated to this section
            sequential_source_ids = section_to_sources.get(section_header, [])
            
            # Map sequential IDs to evidence items
            section_evidence = []
            for seq_id in sequential_source_ids:
                for evidence_item in evidence_base:
                    if evidence_item['id'] == seq_id:
                        section_evidence.append(evidence_item)
                        break
            
            # If no sources mapped, use keyword-based filtering as fallback
            if not section_evidence:
                # Extract keywords from both header and content bullets
                header_keywords = self._extract_keywords_from_header(section_header)
                    
                content_keywords = []
                for bullet in section.get('content', []):
                    content_keywords.extend(self._extract_keywords_from_text(bullet))
                section_keywords = list(set(header_keywords + content_keywords))
                section_evidence = self._filter_evidence_for_section(evidence_base, section_keywords)
                
            # Expand this section with evidence, including the section's content points
            expanded_text = self.expand_markdown_section_with_citations(
            query=query,
            all_sections_so_far=text_so_far,
            section_header=section_header,
            section_content_points=section_content_points,
            section_evidence=section_evidence
            )
            
            # Track which sources were used in this section (by sequential ID)
            sources_used = self._extract_source_references(expanded_text)
            
            # Map the sequential IDs to original result IDs for tracking
            original_ids_used = [source_id_map.get(seq_id) for seq_id in sources_used if seq_id in source_id_map]
            section_sources[section_header] = original_ids_used
            
            # Combine header and expanded content
            section_title = section_header.replace('#', '').strip()

            # More robust check for section title in expanded text
            if (expanded_text.strip().startswith(section_title) or 
                any(expanded_text.strip().startswith(f"{'#'*i} {section_title}") for i in range(1, 7))):
                
                # Find where the actual content begins (after the header and any newlines)
                content_start = expanded_text.find('\n') 
                if content_start > 0:
                    # Skip the first line (which contains the duplicate header)
                    combined_section = f"{section_header}\n{expanded_text[content_start+1:].strip()}"
                else:
                    # Fallback if no newline found
                    combined_section = f"{section_header}\n{expanded_text[len(section_title):].strip()}"
            else:
                # No duplicate title detected, use both
                combined_section = f"{section_header}\n{expanded_text}"

            final_markdown_sections.append(combined_section)
            
            # Enforce token limits - if we're getting too large, summarize earlier sections
            if len("\n\n".join(final_markdown_sections)) > 6000:  # conservative limit
                final_markdown_sections = self._condense_early_sections(final_markdown_sections)
        
        # Step 5: Combine everything into one cohesive Markdown string
        print("Stage 3: Assembling complete answer...")
        assembled_answer = "\n\n".join(final_markdown_sections)
        
        # Step 6: Generate follow-up questions based on the complete answer
        print("Stage 4: Generating follow-up questions...")
        follow_up_questions = self._generate_follow_up_questions_from_answer(query, assembled_answer)
        
        # Step 7: Add a sources section at the end
        sources_section = self._generate_sources_section(search_results, section_sources)
        assembled_answer += f"\n\n{sources_section}"
        
        return {
            "answer": assembled_answer,
            "follow_up_questions": follow_up_questions
        }

    def _flatten_sections(self, hierarchical_sections):
        """
        Flatten a hierarchical section structure into a linear list of all sections and subsections.
        This ensures all headers at any level get processed individually.
        """
        flat_sections = []
        
        def process_section(section):
            # Add the current section
            flat_sections.append(section)
            
            # Process any subsections
            for subsection in section.get('subsections', []):
                process_section(subsection)
        
        # Process each top-level section
        for section in hierarchical_sections:
            process_section(section)
        
        return flat_sections

    def expand_markdown_section_with_citations(self, query, all_sections_so_far, section_header, section_content_points, section_evidence, max_retries=3):
        """
        Expanded version of section expansion that explicitly encourages source citations.
        Includes retry logic for handling JSON parsing failures.
        """
        # Format the evidence strings with page analysis data
        evidence_str = ""
        for evidence in section_evidence:
            evidence_str += f"SOURCE {evidence['id']}: {evidence['title']} ({evidence['url']})\n"
            evidence_str += f"Relevance Score: {evidence.get('relevance_score', 5)}/10\n"
            evidence_str += f"Summary: {evidence['summary']}\n"
            
            # Include key points if available
            key_points = evidence.get('key_points', [])
            if key_points:
                evidence_str += "Key Points:\n"
                for point in key_points:
                    evidence_str += f"- {point}\n"
            
            evidence_str += "\n"
        
        # Base prompt remains the same
        base_prompt = f"""
We have an ongoing answer for the query: "{query}" in Markdown format.

So far, the collected sections are:
{all_sections_so_far}

Now we want to fill out this section in detail:
"{section_header}"

Outline points:
{section_content_points}

Use these relevant sources for this section:
{evidence_str}

**!!WRITE THE ACTUAL SECTION TEXT!!** Don't write '...' or anything that is not the actual content!
Be detailed, use bullet points or subheadings if needed,
and make sure it flows logically from the sections that came before it.

IMPORTANT: 
- Include in-line citations like [Source 1], [Source 2], etc. to attribute information to specific sources.
- Only cite sources that actually support the specific information being stated.
- Do not cite sources for general knowledge.
- Use direct quotes sparingly and always with citation.
- DO NOT repeat the section title at the beginning of your text
- Make it 500 to 1000 words long.
"""

        # Define the JSON schema
        section_schema = {
            "type": "object",
            "properties": {
                "thinking": {
                    "type": "string",
                    "description": "Your step-by-step analysis process and reasoning for the section_text"
                },
                "section_text": {
                    "type": "string",
                    "description": "The Markdown content for this section with citations, 500 to 1000 words long. WRITE THE ACTUAL SECTION TEXT HERE! Don't write '...' or anything that is not the actual content."
                }
            },
            "required": ["thinking", "section_text"]
        }

        # Try multiple times with different approaches
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt+1} for section: {section_header}")
                
                # Only use schema for all attempts - but adjust prompts 
                if attempt == 0:
                    prompt = base_prompt + "\nReturn your content in the specified JSON format."
                elif attempt == 1:
                    prompt = base_prompt + """
IMPORTANT: Ensure you return a valid JSON object with 'thinking' and 'section_text' fields.
Be sure to properly escape any quotes or special characters to ensure valid JSON.
"""
                else:
                    prompt = base_prompt + """
IMPORTANT: Return only well-formatted JSON with proper escaping of all special characters.
Focus on creating valid, parseable JSON while maintaining the quality of your content.
"""
                
                # Always use schema for consistency
                response_obj = self.generate_response(
                    prompt=prompt,
                    schema=section_schema,
                    temperature=0.7,
                    backend="openai"
                )
                
                # Process response - should be a dictionary if schema worked
                if isinstance(response_obj, dict):
                    section_text = response_obj.get("section_text", "")
                    if not isinstance(section_text, str):
                        raise ValueError(f"Invalid section_text in response (attempt {attempt+1})")
                    return section_text
                else:
                    raise ValueError(f"Response is not a dictionary (attempt {attempt+1})")
                    
            except Exception as e:
                print(f"Error in expand_markdown_section_with_citations (attempt {attempt+1}): {e}")
                traceback.print_exc()
                if attempt == max_retries - 1:
                    # Last attempt failed, use fallback
                    break
                # Otherwise continue to next attempt
        
        # If all attempts failed, create a simple fallback content
        print(f"All {max_retries} attempts to generate content failed. Using fallback content.")
        return f"This section could not be generated automatically due to technical limitations. Here's what we know about {section_header.replace('#', '').strip()}:\n\n" + \
                "\n\n".join([f"- Information from {ev['title']}: {ev.get('summary', '')[:150]}..." for ev in section_evidence[:2]])
                
    # Add a helper method to fix common JSON issues with quotes
    def _fix_json_quotes(self, json_str):
        """
        Fix common JSON syntax issues with quotes inside strings.
        This is a best-effort approach and may not handle all edge cases.
        """
        # Check if we have a common pattern of unescaped quotes in the section_text value
        if '"section_text": "' in json_str:
            # Split into parts
            prefix = json_str.split('"section_text": "')[0] + '"section_text": "'
            content = json_str.split('"section_text": "')[1]
            
            # Find the proper end of the string (last quote before final })
            if content.endswith('"}') or content.endswith('" }'):
                # Content is already properly terminated
                return json_str
                
            # Escape internal quotes in the content
            fixed_content = ""
            in_markdown_code_block = False
            
            for i, char in enumerate(content):
                if char == '`' and content[i:i+3] == '```':
                    in_markdown_code_block = not in_markdown_code_block
                    fixed_content += char
                elif char == '"' and not in_markdown_code_block:
                    # Check if this seems to be the closing quote
                    remainder = content[i+1:].strip()
                    if remainder == "}" or remainder.startswith("}"):
                        # This is likely the closing quote, add it and stop
                        return prefix + fixed_content + '"' + remainder
                    else:
                        # This is an internal quote, escape it
                        fixed_content += '\\"'
                else:
                    fixed_content += char
                    
            # If we couldn't find a proper end, just return the original
            return json_str
        else:
            # Different format or already fixed
            return json_str

    def _build_evidence_base(self, search_results):
        """Create a structured evidence base from search results, leveraging page analysis."""
        evidence = []
        for idx, result in enumerate(search_results):
            if 'url' not in result or not result['url']:
                continue
            
            # Check if we have page analysis data
            page_analysis = result.get('page_analysis', {})
            
            # Get the summary and key points from page analysis
            summary = page_analysis.get('summary', '')
            key_points = page_analysis.get('key_points', [])
            relevance_score = page_analysis.get('relevance_score', 5)
            
            # Fallback to snippet if no analysis available
            if not summary and not key_points:
                summary = result.get('snippet', 'No content available')[:300]
                key_points = ['No key points available']
            
            # Add to evidence base with streamlined structure
            evidence.append({
                'id': idx + 1,
                'title': result.get('title', f'Source {idx+1}'),
                'url': result.get('url', 'No URL'),
                'summary': summary,
                'key_points': key_points,
                'relevance_score': relevance_score
            })
        
        # Sort evidence by relevance score (highest first)
        evidence.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return evidence

    def _parse_markdown_outline(self, outline):
        """
        Enhanced Markdown outline parser that respects header hierarchy.
        Creates a nested structure where H2s are children of H1s, and H3s are children of H2s.
        """
        if not outline or not isinstance(outline, str):
            return []
            
        lines = outline.split('\n')
        sections = []
        current_headers = {1: None, 2: None, 3: None}  # Track current headers at each level
        header_pattern = re.compile(r'^(#{1,3})\s+(.+)')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for headers (# Header, ## Header, or ### Header)
            match = header_pattern.match(line)
            if match:
                # Found a header
                header_markers = match.group(1)  # The # symbols
                header_level = len(header_markers)  # Number of # symbols (1, 2, or 3)
                header_text = match.group(2)  # The actual header text
                
                # Create new section object
                new_section = {
                    'header': line,
                    'level': header_level,
                    'title': header_text,
                    'content': [],
                    'subsections': []
                }
                
                # Handle based on header level
                if header_level == 1:  # H1 - top level
                    sections.append(new_section)
                    current_headers[1] = new_section
                    current_headers[2] = None
                    current_headers[3] = None
                elif header_level == 2:  # H2 - second level
                    if current_headers[1]:  # If we have a parent H1
                        current_headers[1]['subsections'].append(new_section)
                    else:  # No parent, treat as top-level
                        sections.append(new_section)
                    current_headers[2] = new_section
                    current_headers[3] = None
                elif header_level == 3:  # H3 - third level
                    if current_headers[2]:  # If we have a parent H2
                        current_headers[2]['subsections'].append(new_section)
                    elif current_headers[1]:  # No H2 parent but H1 exists
                        current_headers[1]['subsections'].append(new_section)
                    else:  # No parents, treat as top-level
                        sections.append(new_section)
                    current_headers[3] = new_section
            elif any(current_headers.values()):  # Content line (not a header)
                # Add to the most specific current header's content
                for level in [3, 2, 1]:
                    if current_headers[level]:
                        current_headers[level]['content'].append(line)
                        break
                
        return sections

    def _extract_keywords_from_header(self, header_text):
        """Extract key terms from a section header."""
        # Remove Markdown formatting and convert to lowercase
        clean_header = re.sub(r'^#+\s+', '', header_text).lower()
        
        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about'}
        words = [word for word in re.findall(r'\w+', clean_header) if word.lower() not in stop_words]
        
        return words

    def _extract_keywords_from_text(self, text):
        """Extract keywords from text content."""
        # Simple keyword extraction - would be better with NLP in a production system
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about',
                     'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                     'this', 'that', 'these', 'those', 'they', 'them', 'their', 'it', 'its'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if word not in stop_words and len(word) > 3]

    def _filter_evidence_for_section(self, evidence_base, section_keywords):
        """Filter evidence to find relevant pieces for a specific section."""
        if not section_keywords:
            return evidence_base  # Return all if no keywords
            
        relevant_evidence = []
        for evidence in evidence_base:
            # Calculate relevance score as keyword overlap
            evidence_keywords = evidence.get('keywords', [])
            overlap = len(set(section_keywords) & set(evidence_keywords))
            
            if overlap > 0 or len(section_keywords) == 0:
                relevant_evidence.append(evidence)
        
        # If we found no relevant evidence, return all evidence
        if not relevant_evidence:
            return evidence_base
            
        return relevant_evidence

    def _extract_source_references(self, text):
        """Extract source reference IDs from a text with citations like [Source 1]."""
        source_refs = set()
        matches = re.findall(r'\[Source\s+(\d+)\]', text)
        for match in matches:
            try:
                source_refs.add(int(match))
            except ValueError:
                continue
        return sorted(list(source_refs))

    def _condense_early_sections(self, sections):
        """Condense earlier sections if the total content is getting too large."""
        if len(sections) <= 2:
            return sections  # Need at least intro, main content
            
        # Keep first and last sections intact, summarize middle sections
        condensed = [sections[0]]  # Keep introduction
        
        # For middle sections, keep headers but summarize content
        middle_sections_text = "\n\n".join(sections[1:-1])
        middle_sections_summary = self._summarize_text(middle_sections_text)
        
        condensed.append(f"## Main Points\n{middle_sections_summary}")
        condensed.append(sections[-1])  # Keep conclusion
        
        return condensed

    def _summarize_text(self, text, max_length=1000):
        """Summarize a long text to a shorter version."""
        if len(text) <= max_length:
            return text
            
        prompt = f"""Summarize the following text into a concise but comprehensive summary:

{text[:5000]}  # Limit input to avoid token limits

Return ONLY the summary text with no additional explanation or formatting.
The summary should be no more than {max_length} characters.
"""
        try:
            return self.generate_response(prompt)
        except:
            # If summarization fails, truncate with ellipsis
            return text[:max_length] + "... [content truncated for length]"

    def _generate_follow_up_questions_from_answer(self, query, answer_text):
        """Generate follow-up questions based on the complete answer."""
        prompt = f"""Based on this comprehensive answer to the query "{query}":

{answer_text[:4000]}  # Limit input to avoid token limits

Generate 3 thoughtful follow-up questions that would help the user explore this topic further.
Each question should address a different aspect of the topic.

Return ONLY a JSON object with the following format:
{{
  "questions": [
    "First follow-up question?",
    "Second follow-up question?",
    "Third follow-up question?"
  ]
}}
"""
        try:
            response_text = self.generate_response(prompt)
            # Remove code fence markers
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                
            json_obj = json.loads(response_text)
            questions = json_obj.get("questions", [])
            
            # Ensure we have exactly 3 questions
            while len(questions) < 3:
                questions.append(f"Can you elaborate more on {query}?")
                
            return questions[:3]
        except:
            # Fallback questions if generation fails
            return [
                f"What are the most important factors affecting {query}?",
                f"How might {query} change in the future?",
                f"What are some alternative perspectives on {query}?"
            ]

    def _generate_sources_section(self, search_results, section_sources):
        """Generate a sources section listing all sources used in the answer."""
        # Create a mapping from original result IDs to details and sequential display IDs
        source_map = {}
        display_id_map = {}  # Maps original IDs to sequential display numbers
        
        # First, create mapping of original IDs to source details
        for idx, result in enumerate(search_results):
            if 'url' not in result or not result['url']:
                continue
                
            original_id = result.get('id')
            if original_id:
                source_map[original_id] = {
                    'title': result.get('title', f'Source {idx+1}'),
                    'url': result.get('url', 'No URL'),
                }
        
        # Get all unique original source IDs referenced across all sections
        all_sources = set()
        for sources in section_sources.values():
            all_sources.update(sources)
        
        # Generate the source list with sequential display numbers
        sources_md = "## Sources\n\n"
        for display_num, original_id in enumerate(sorted(all_sources), start=1):
            if original_id in source_map:
                source = source_map[original_id]
                sources_md += f"{display_num}. [{source['title']}]({source['url']})\n"
        
        return sources_md

    def detect_query_intent(self, query, clarification_responses=None):
        """
        Determine if a query is a research question or a direct information request.
        
        Args:
            query: The original query
            clarification_responses: Optional clarification responses
            
        Returns:
            Dictionary with "intent" (research_question/information_request) and "explanation"
        """
        # Format clarifications if any
        clarifications_text = ""
        if clarification_responses:
            for resp in clarification_responses:
                clarifications_text += f"- Question: {resp['question']}\n  Answer: {resp['answer']}\n"
        
        prompt = f"""Analyze this user query: "{query}"
        
    Additional context from clarifications:
    {clarifications_text if clarifications_text else "No clarifications provided."}

    Determine if this query is:
    1. A RESEARCH QUESTION: Complex, exploratory, seeking to understand relationships, mechanisms, or deeper insights requiring synthesis of multiple sources. Often starts with "how", "why", "what factors", etc.
    2. An INFORMATION REQUEST: Seeking specific facts, direct answers, recommendations, or instructions. Often practical, immediate, or looking for concrete information.

    Examples:
    - "What factors influence climate change?" → research_question
    - "Where can I stay in Tel Aviv tonight?" → information_request
    - "How does social media affect teenage mental health?" → research_question
    - "What's the best recipe for chocolate cake?" → information_request
    """
        
        # Define schema for structured output
        intent_schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["research_question", "information_request"],
                    "description": "The type of query (research_question or information_request)"
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of why the query was classified this way"
                }
            },
            "required": ["intent", "explanation"]
        }
        
        try:
            result = self.generate_response(prompt, temperature=0.3, schema=intent_schema)
            return result
        except Exception as e:
            print(f"Error in detecting query intent: {e}")
            # Default fallback
            return {"intent": "information_request", "explanation": "Error in detection"}

    def generate_improved_query(self, original_query, clarification_responses):
        """
        Generate an improved query based on original query and clarifications,
        maintaining the original intent (research question or direct information request).
        
        Args:
            original_query: The user's original search query
            clarification_responses: List of dicts with 'question' and 'answer' keys
            
        Returns:
            An improved query that preserves the original intent
        """
        # First, detect the intent of the query
        intent_result = self.detect_query_intent(original_query, clarification_responses)
        query_intent = intent_result.get("intent", "information_request")
        
        # Format clarification responses
        clarifications_text = ""
        if clarification_responses:
            for i, resp in enumerate(clarification_responses):
                clarifications_text += f"Question {i+1}: {resp['question']}\n"
                clarifications_text += f"Answer {i+1}: {resp['answer']}\n\n"
        
        if query_intent == "research_question":
            # For research questions, use academic formatting
            prompt = f"""You are a research methodology expert helping to formulate an academic research question.

    ORIGINAL QUERY: {original_query}

    CLARIFICATIONS:
    {clarifications_text if clarifications_text else "No additional clarifications were provided."}

    Based on the original query and these clarifications, create a formal research question that:
    1. Is clear, concise, and open-ended (not answerable with yes/no)
    2. Begins with words like "How," "What," "Why," "To what extent," or similar interrogative phrases
    3. Is specific enough to be answerable through research
    4. Identifies the central phenomenon or relationship being investigated
    5. Is neutral and does not presuppose a particular answer
    6. Contains only one main question (not multiple questions combined)
    7. Is suitable for academic inquiry or a formal research paper

    Examples of good research questions:
    - "How does exposure to social media affect adolescents' self-perception?"
    - "What factors contribute to the resilience of coral reef ecosystems under climate change?"
    - "To what extent do economic incentives influence renewable energy adoption in developing countries?"

    Return ONLY the research question without any explanations or additional text.
    """
        else:
            # For direct information requests, preserve intent while improving clarity
            prompt = f"""You are an expert search assistant helping to improve a user's query.

    ORIGINAL QUERY: {original_query}

    CLARIFICATIONS:
    {clarifications_text if clarifications_text else "No additional clarifications were provided."}

    Based on the original query and these clarifications, create an improved search query that:
    1. Maintains the original intent and request type
    2. Is clear, specific, and unambiguous
    3. Includes important details from the clarifications
    4. Would work well for finding the exact information needed
    5. Is written in natural, conversational language
    6. Is direct and to the point
    7. Do not return a question to the user

    Examples:
    - Original: "hotels tel aviv"
    Improved: "What are the best hotels to stay in Tel Aviv tonight with availability?"
    - Original: "chocolate cake recipe"
    Improved: "What's a highly-rated chocolate cake recipe that's easy to make?"

    Return ONLY the improved query without any explanations or additional text.
    """
        
        try:
            improved_query = self.generate_response(prompt, temperature=0.3)
            
            # Ensure proper formatting based on intent
            if query_intent == "research_question" and not improved_query.strip().endswith('?'):
                improved_query = improved_query.strip() + '?'
                
            # Ensure reasonable length
            if len(improved_query) > 150:
                improved_query = improved_query[:147] + "...?"
            
            return improved_query
        except Exception as e:
            print(f"Error generating improved query: {e}")
            return original_query
# ------------------------------- Page understanding --------------------------------
    def generate_page_understanding(self, enhanced_query, content, url="", title="", max_length=500):
        """
        Generate a concise understanding of webpage content, evaluating its relevance to a specific query.
        
        Args:
            enhanced_query: The user's enhanced search query
            content: The extracted content of the page
            url: The URL of the page (optional)
            title: The page title (optional)
            max_length: Maximum length of understanding
            
        Returns:
            A dictionary with summary, relevance_score, and key_points
        """
        # Truncate content to a reasonable length
        max_content_length = 15000
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "... [content truncated]"
        
        prompt = f"""Please analyze this web page content in relation to the following query:
        
    QUERY: {enhanced_query}

    URL: {url}
    TITLE: {title}
        
    CONTENT:
    {truncated_content}

    Analyze the content and provide:
    1. A concise summary (max {max_length} chars)
    2. A relevance score from 1-10 (10 being highly informative and credible specifically for answering the query)
    3. 3-5 key points extracted from the content that are most relevant to the query

    Focus your analysis on how well the content addresses the specific query.
    """
        
        # Define a schema for structured output
        understanding_schema = {
            "type": "object",
            "properties": {
                "thinking": {
                    "type": "string",
                    "description": "Your step-by-step analysis process and reasoning for the summary, relevance score, and key points, especially how they relate to the query"
                },
                "summary": {
                    "type": "string",
                    "description": f"Concise summary of the page content (max {max_length} chars)"
                },
                "relevance_score": {
                    "type": "integer",
                    "description": "Score from 1-10 indicating information quality and relevance to the query",
                    "minimum": 1,
                    "maximum": 10
                },
                "key_points": {
                    "type": "array",
                    "description": "3-5 key points from the content most relevant to the query",
                    "items": {"type": "string"}
                }
            },
            "required": ["thinking", "summary", "relevance_score", "key_points"]
        }
        
        try:
            # Get structured understanding using the schema
            result = self.generate_response(prompt, temperature=0.3, schema=understanding_schema)
            return result
        except Exception as e:
            print(f"Error generating page understanding: {e}")
            # Fallback to simple text summary
            try:
                simple_summary = self.generate_response(
                    f"Summarize this content in relation to the query '{enhanced_query}':\n\n{content[:8000]}", 
                    temperature=0.3
                )
                return {
                    "summary": simple_summary, 
                    "relevance_score": 5, 
                    "key_points": ["Content could not be fully analyzed"]
                }
            except:
                return {
                    "summary": "Failed to analyze page content", 
                    "relevance_score": 0, 
                    "key_points": ["Analysis failed"]
                }