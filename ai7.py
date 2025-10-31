from crewai import Agent, LLM
from dotenv import load_dotenv
import os
import json
import datetime
import google.generativeai as genai
from typing import List, Dict
import numpy as np

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
load_dotenv()

llm = LLM(
    model="gemini/gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY")
)

class ProductRAG:
    """RAG system for product recommendations"""
    
    def __init__(self, products_json_path: str = "rproducts.json"):
        self.products = self._load_products(products_json_path)
        self.genai_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
    def _load_products(self, path: str) -> List[Dict]:
        """Load products from JSON file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'products' in data:
                    return data['products']
                else:
                    return [data]  # Single product object
        except FileNotFoundError:
            print(f"Warning: {path} not found. Using empty product list.")
            return []
    
    def search_products(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search products using semantic similarity with Gemini embeddings
        Falls back to keyword search if embedding fails
        """
        if not self.products:
            return []
        
        try:
            # Use Gemini to find relevant products
            product_context = self._format_products_for_context(self.products[:50])  # Limit context size
            
            search_prompt = f"""
Given these products:
{product_context}

User query: {query}

Return the {top_k} most relevant product names that match this query.
Consider: category, price range, features, and user intent.
Return ONLY a JSON array of product names, nothing else.
Example: ["Product A", "Product B", "Product C"]
"""
            
            response = self.genai_model.generate_content(search_prompt)
            product_names = json.loads(response.text.strip())
            
            # Get full product details
            relevant_products = [
                p for p in self.products 
                if p.get('name') in product_names or p.get('title') in product_names
            ]
            
            return relevant_products[:top_k]
            
        except Exception as e:
            print(f"Semantic search failed: {e}. Falling back to keyword search.")
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Fallback keyword-based search"""
        query_lower = query.lower()
        scored_products = []
        
        for product in self.products:
            score = 0
            searchable_text = json.dumps(product).lower()
            
            # Simple scoring based on query terms
            for term in query_lower.split():
                if len(term) > 2:  # Ignore very short words
                    score += searchable_text.count(term)
            
            if score > 0:
                scored_products.append((score, product))
        
        # Sort by score and return top_k
        scored_products.sort(reverse=True, key=lambda x: x[0])
        return [p[1] for p in scored_products[:top_k]]
    
    def _format_products_for_context(self, products: List[Dict]) -> str:
        """Format products for LLM context"""
        formatted = []
        for i, p in enumerate(products, 1):
            # Handle different JSON structures
            name = p.get('name') or p.get('title') or p.get('product_name', 'Unknown')
            price = p.get('price') or p.get('cost', 'N/A')
            category = p.get('category') or p.get('type', 'General')
            description = p.get('description', '')[:100]  # Limit length
            
            formatted.append(
                f"{i}. {name} | Category: {category} | Price: {price} | {description}"
            )
        return "\n".join(formatted)
    
    def get_product_details(self, product_names: List[str]) -> List[Dict]:
        """Get full details for specific products"""
        return [
            p for p in self.products
            if p.get('name') in product_names or p.get('title') in product_names
        ]


class ConversationalCrew:
    def __init__(self, agents, products_json_path: str = "products.json"):
        self.agents = agents
        self.product_rag = ProductRAG(products_json_path)  # Initialize RAG
        self.context = {
            "conversation_history": [],
            "user_preferences": {},
            "products_mentioned": [],
            "cart_items": [],
            "customer_info": {},
            "issues_reported": [],
            "recommendations_given": [],
            "transactions": [],
            "loyalty_points": 0,
            "follow_ups": [],
            "session_metadata": {
                "start_time": None,
                "last_interaction": None,
                "interaction_count": 0
            }
        }
        
        self.genai_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.agent_tools = self._create_gemini_tools()

    def _create_gemini_tools(self):
        """Create Gemini function declarations for each agent"""
        function_declarations = []
        
        for agent in self.agents:
            function_declarations.append(
                genai.protos.FunctionDeclaration(
                    name=agent.role.lower().replace(" ", "_"),
                    description=f"Role: {agent.role}. Goal: {agent.goal}. Backstory: {agent.backstory}",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "response": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="The agent's response to the user in first-person tone"
                            ),
                            "cart_items": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                description="Products to add to cart",
                                items=genai.protos.Schema(type=genai.protos.Type.STRING)
                            ),
                            "products_mentioned": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                description="Products discussed in conversation",
                                items=genai.protos.Schema(type=genai.protos.Type.STRING)
                            ),
                            "loyalty_points": genai.protos.Schema(
                                type=genai.protos.Type.NUMBER,
                                description="Updated loyalty points if applicable"
                            ),
                            "issue_reported": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="Any technical issue or complaint reported"
                            )
                        },
                        required=["response"]
                    )
                )
            )
        
        return genai.protos.Tool(function_declarations=function_declarations)
    
    def _get_rag_context(self, user_input: str) -> str:
        """Get relevant products using RAG for recommendation queries"""
        # Keywords that indicate a recommendation/search query
        recommendation_keywords = [
            'recommend', 'suggest', 'looking for', 'need', 'want', 
            'show me', 'find', 'search', 'buy', 'purchase', 'get'
        ]
        
        user_input_lower = user_input.lower()
        is_recommendation_query = any(keyword in user_input_lower for keyword in recommendation_keywords)
        
        if is_recommendation_query:
            # Retrieve relevant products
            relevant_products = self.product_rag.search_products(user_input, top_k=5)
            
            if relevant_products:
                return self.product_rag._format_products_for_context(relevant_products)
        
        return "No specific products retrieved for this query."
    
    def route_message(self, user_input):
        """Single LLM call that decides agent AND generates response with RAG"""
        
        # Update session metadata
        if self.context["session_metadata"]["start_time"] is None:
            self.context["session_metadata"]["start_time"] = datetime.datetime.now().isoformat()
        
        self.context["session_metadata"]["last_interaction"] = datetime.datetime.now().isoformat()
        self.context["session_metadata"]["interaction_count"] += 1
        
        # Build context summary
        recent_history = self.context["conversation_history"][-5:]
        context_text = "\n".join(
            [f"User: {m['user']}\n{m['agent']}: {m['reply']}" for m in recent_history]
        ) if recent_history else "No previous conversation"
        
        # Get RAG context (relevant products)
        rag_context = self._get_rag_context(user_input)
        
        # Create comprehensive prompt with RAG
        prompt = f"""
You are a multi-agent customer service system for an e-commerce platform.
Analyze the user's message and call the MOST APPROPRIATE agent function to respond.

CURRENT CONTEXT:
- Cart Items: {self.context['cart_items']}
- Products Mentioned: {self.context['products_mentioned'][-10:] if self.context['products_mentioned'] else 'None'}
- Loyalty Points: {self.context['loyalty_points']}
- Customer Info: {self.context['customer_info']}
- Active Issues: {len(self.context['issues_reported'])} reported

RECENT CONVERSATION:
{context_text}

RELEVANT PRODUCTS (from database):
{rag_context}

USER MESSAGE: {user_input}

Instructions:
1. Choose the most appropriate agent based on the user's intent
2. If this is a recommendation/product query, USE THE RELEVANT PRODUCTS listed above
3. Generate a helpful, personalized response as that agent
4. Extract any relevant data (cart items, products, issues, etc.)
5. Stay in character for the chosen agent
6. When recommending products, reference the specific products from the database above
"""
        
        try:
            # SINGLE LLM CALL with function calling
            response = self.genai_model.generate_content(
                contents=prompt,
                tools=[self.agent_tools],
                tool_config={'function_calling_config': 'ANY'}
            )
            
            # Process response
            for part in response.parts:
                if part.function_call:
                    function_call = part.function_call
                    agent_function_name = function_call.name
                    
                    function_args = {}
                    for key, value in function_call.args.items():
                        function_args[key] = value
                    
                    agent_name = agent_function_name.replace("_", " ").title()
                    reply = function_args.get("response", "I'm here to help!")
                    
                    # Extract and update context data
                    if "cart_items" in function_args:
                        new_items = list(function_args["cart_items"])
                        self.context["cart_items"].extend(new_items)
                    
                    if "products_mentioned" in function_args:
                        new_products = list(function_args["products_mentioned"])
                        self.context["products_mentioned"].extend(new_products)
                        # Track recommendations
                        if agent_name == "Data Analyst":  # Recommendation agent
                            self.context["recommendations_given"].extend(new_products)
                    
                    if "loyalty_points" in function_args:
                        self.context["loyalty_points"] = int(function_args["loyalty_points"])
                    
                    if "issue_reported" in function_args:
                        self.context["issues_reported"].append({
                            "issue": function_args["issue_reported"],
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    
                    # Store in conversation history
                    self.context["conversation_history"].append({
                        "user": user_input,
                        "agent": agent_name,
                        "reply": reply,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    return agent_name, reply
                
                elif part.text:
                    text_response = part.text
                    self.context["conversation_history"].append({
                        "user": user_input,
                        "agent": "General Assistant",
                        "reply": text_response,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    return "General Assistant", text_response
            
            raise ValueError("No valid response from model")
                
        except Exception as e:
            import traceback
            error_msg = f"I apologize, I encountered an error: {str(e)}"
            print(f"\nDebug - Full error:\n{traceback.format_exc()}")
            return "Error Handler", error_msg
    
    def get_context_summary(self):
        """Get a summary of all stored context data"""
        return {
            "total_interactions": self.context["session_metadata"]["interaction_count"],
            "session_start": self.context["session_metadata"]["start_time"],
            "cart_items": self.context["cart_items"],
            "products_discussed": len(self.context["products_mentioned"]),
            "unique_products": len(set(self.context["products_mentioned"])),
            "issues_count": len(self.context["issues_reported"]),
            "loyalty_points": self.context["loyalty_points"],
            "recommendations_made": len(self.context["recommendations_given"]),
            "total_products_in_db": len(self.product_rag.products)
        }


class MeetingPrepAgents:
    Sales_Agent = Agent(
        role="Sales Specialist",
        goal="Drive sales and meet performance targets by upselling and cross selling products.",
        backstory="Experienced in sales strategies and customer engagement. Subtly influences customer decisions to maximize revenue.",
        llm=llm,
        verbose=False
    )
    Recommendation_Agent = Agent(
        role="Data Analyst",
        goal="Analyze items available in the store and make personalized recommendations based on product database.",
        backstory="Expert in product analytics with access to comprehensive product database. Uses data-driven insights to match customers with perfect products.",
        llm=llm,
        verbose=False
    )

    Inventory_Agent = Agent(
        role="Inventory Specialist",
        goal="Manage inventory levels and stock availability.",
        backstory="Detail-oriented and experienced in inventory management.",
        llm=llm,
        verbose=False
    )

    Cart_Agent = Agent(
        role="Shopping Cart Specialist",
        goal="Manage shopping cart operations and user interactions.",
        backstory="Experienced in e-commerce and user experience.",
        llm=llm,
        verbose=False
    )

    Fulfillment_Agent = Agent(
        role="Logistics Coordinator",
        goal="Coordinate logistics and ensure timely delivery of items.",
        backstory="Detail-oriented and efficient in managing supply chains.",
        llm=llm,
        verbose=False
    )

    Payment_Agent = Agent(
        role="Financial Transactions Expert",
        goal="Handle payment processing and financial records.",
        backstory="Skilled in secure and efficient payment systems.",  
        llm=llm,
        verbose=False
    )

    Post_Purchase_Agent = Agent(
        role="Customer Relations Specialist",
        goal="Manage post-purchase follow-ups and customer satisfaction.",
        backstory="Focused on building strong customer relationships.",
        llm=llm,
        verbose=False
    )
    
    Loyalty_and_Offers_Agent = Agent(
        role="Customer Loyalty Specialist",
        goal="Manage customer loyalty programs and special offers.",
        backstory="Expert in enhancing customer retention through rewards.",
        llm=llm,
        verbose=False
    )

    CRM_Agent = Agent(
        role="Customer Relationship Manager",
        goal="Maintain and update customer relationship management systems.",
        backstory="Proficient in CRM tools and customer data analysis.",
        llm=llm,
        verbose=False
    )

    Error_Handling_Agent = Agent(
        role="Technical Support Specialist",
        goal="Identify and resolve technical issues in the shopping process.",
        backstory="Experienced in troubleshooting and customer support.",
        llm=llm,
        verbose=False
    )


# Create the conversational crew with RAG
crew = ConversationalCrew(
    agents=[
        MeetingPrepAgents.Sales_Agent,
        MeetingPrepAgents.Recommendation_Agent,
        MeetingPrepAgents.Inventory_Agent,
        MeetingPrepAgents.Cart_Agent,
        MeetingPrepAgents.Fulfillment_Agent,
        MeetingPrepAgents.Payment_Agent,
        MeetingPrepAgents.Post_Purchase_Agent,
        MeetingPrepAgents.Loyalty_and_Offers_Agent,
        MeetingPrepAgents.CRM_Agent,
        MeetingPrepAgents.Error_Handling_Agent,
    ],
    products_json_path="rproducts.json"  # Specify your JSON file path
)

print("### CrewAI with RAG-Enhanced Recommendations ###")
print(f"Loaded {len(crew.product_rag.products)} products from database")
print("Type 'exit' to quit, 'summary' to see context summary.\n")


while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("\n=== Session Summary ===")
        summary = crew.get_context_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nGoodbye!")
        break
    
    if user_input.lower() == "summary":
        print("\n=== Current Context Summary ===")
        summary = crew.get_context_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        print()
        continue

    print("Thinking...", end="", flush=True)
    agent_name, reply = crew.route_message(user_input)
    print("\r" + " " * 20 + "\r", end="", flush=True)
    print(f"{agent_name}: {reply}\n")