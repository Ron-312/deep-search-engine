# Template for checking if the query needs clarification
CLARIFICATION_PROMPT = """
Analyze the following search query and determine if it needs further clarification.
If it does need clarification, generate up to 3 questions to ask the user that would help clarify the query.
If it doesn't need clarification, indicate that it's clear enough.

Query: {query}

Respond in the following JSON format:
{{
  "needs_clarification": true/false,
  "explanation": "Brief explanation of why the query needs/doesn't need clarification",
  "questions": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ]
}}

If the query is clear, set "needs_clarification" to false and provide an empty array for "questions".
"""

# Template for generating optimized search queries
SEARCH_QUERY_PROMPT = """
I want to search the web for information about the following query:

{query}

Please convert this into an optimized search query that will yield the most relevant results.
Focus on the key concepts and use search operators if helpful.
Return only the optimized search query without any additional text or explanations.
"""

# Template for generating intermediate answers
INTERMEDIATE_ANSWER_PROMPT = """
Based on the following search query and search results, provide an intermediate understanding of the topic.
This is not the final answer, so focus on summarizing what you've learned so far and identifying gaps that need further research.

Query: {query}

Search Results:
{results}

Provide a concise intermediate understanding based on these results:
"""

# Template for generating final answers
ANSWER_PROMPT = """
Based on the following search query and search results, provide a comprehensive and accurate answer.

Query: {query}

Search Results:
{results}

Provide a detailed answer that synthesizes information from all the sources. Include specific information from the sources when relevant.
"""

# Template for generating follow-up search queries
FOLLOW_UP_QUESTIONS_PROMPT = """
Based on the original query and the search results so far, generate {max_queries} follow-up search queries that would help gather additional relevant information.

Original Query: {query}

Search Results So Far:
{results}

Generate {max_queries} follow-up search queries that:
1. Address aspects not covered in the current results
2. Dig deeper into specific details mentioned in the results
3. Explore related concepts that would enhance the overall understanding

Your follow-up queries:
"""

# Template for generating final answers with follow-up questions
ANSWER_WITH_QUESTIONS_PROMPT = """
Based on the following search query and all search results, provide a comprehensive answer and suggest follow-up questions.

Query: {query}

Combined Search Results:
{results}

Respond in the following JSON format:
{{
  "answer": "Your comprehensive, well-structured answer here...",
  "follow_up_questions": [
    "Follow-up question 1?",
    "Follow-up question 2?",
    "Follow-up question 3?"
  ]
}}

Make the answer thorough, accurate, and well-organized. Include specific information from the sources when relevant.
The follow-up questions should address aspects that would be natural next steps in exploring this topic.
"""