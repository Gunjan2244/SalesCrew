from crewai import Agent, LLM
from dotenv import load_dotenv
import os
import json
import datetime
import google.generativeai as genai
from typing import List, Dict, Tuple
import numpy as np

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
load_dotenv()

llm = LLM(
    model="gemini/gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY")
)

class ProductRAGWithEmbeddings:
    """Proper RAG system using embeddings and cosine similarity"""
    
    def __init__(self, products_json_path: str = "rproducts.json"):
        self.products = self._load_products(products_json_path)
        self.product_embeddings = None
        self.embeddings_generated = False
        
    def _load_products(self, path: str) -> List[Dict]:
        """Load products from JSON file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'products' in data:
                    return data['products']
                else:
                    return [data]
        except FileNotFoundError:
            print(f"Warning: {path} not found. Using empty product list.")
            return []
    
    def _prepare_product_text(self, product: Dict) -> str:
        """Convert product dict to searchable text for embedding"""
        name = product.get('name') or product.get('title', 'Unknown')
        category = product.get('category') or product.get('type', '')
        description = product.get('description', '')
        price = str(product.get('price', ''))
        features = product.get('features', '')
        
        text = f"{name} {category} {description} {features} {price}"
        return text.strip()
    
    def generate_embeddings(self):
        """
        ONE-TIME PREPROCESSING: Generate embeddings for all products
        Call this once when initializing the system
        """
        if self.embeddings_generated:
            print("✓ Embeddings already generated")
            return
        
        if not self.products:
            print("⚠ No products to embed")
            return
        
        print(f"🔄 Generating embeddings for {len(self.products)} products...")
        
        embeddings_list = []
        
        for i, product in enumerate(self.products):
            product_text = self._prepare_product_text(product)
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=product_text,
                task_type="retrieval_document"
            )
            
            embeddings_list.append(result['embedding'])
            
            if (i + 1) % 50 == 0 or (i + 1) == len(self.products):
                print(f"  Progress: {i + 1}/{len(self.products)} products")
        
        self.product_embeddings = np.array(embeddings_list)
        self.embeddings_generated = True
        
        print(f"✓ Embeddings generated: {self.product_embeddings.shape}")
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def search_products(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search products using embedding similarity
        Returns: List of relevant products (without scores for backward compatibility)
        """
        if not self.embeddings_generated:
            print("⚠ Embeddings not generated yet! Using fallback search.")
            return self._keyword_search(query, top_k)
        
        if not self.products:
            return []
        
        # Generate query embedding
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = np.array(result['embedding'])
        
        # Calculate similarities with all products
        similarities = []
        for i, product_emb in enumerate(self.product_embeddings):
            similarity_score = self.cosine_similarity(query_embedding, product_emb)
            similarities.append((i, similarity_score))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k products
        top_results = [self.products[i] for i, score in similarities[:top_k]]
        return top_results
    
    def search_products_with_scores(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search products and return with similarity scores
        Useful for debugging or showing confidence
        """
        if not self.embeddings_generated:
            return [(p, 0.0) for p in self._keyword_search(query, top_k)]
        
        if not self.products:
            return []
        
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = np.array(result['embedding'])
        
        similarities = []
        for i, product_emb in enumerate(self.product_embeddings):
            similarity_score = self.cosine_similarity(query_embedding, product_emb)
            similarities.append((i, similarity_score))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [(self.products[i], score) for i, score in similarities[:top_k]]
    
    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Fallback keyword-based search if embeddings fail"""
        query_lower = query.lower()
        scored_products = []
        
        for product in self.products:
            score = 0
            searchable_text = json.dumps(product).lower()
            
            for term in query_lower.split():
                if len(term) > 2:
                    score += searchable_text.count(term)
            
            if score > 0:
                scored_products.append((score, product))
        
        scored_products.sort(reverse=True, key=lambda x: x[0])
        return [p[1] for p in scored_products[:top_k]]
    
    def _format_products_for_context(self, products: List[Dict]) -> str:
        """Format products for LLM context"""
        formatted = []
        for i, p in enumerate(products, 1):
            name = p.get('name') or p.get('title') or p.get('product_name', 'Unknown')
            price = p.get('price') or p.get('cost', 'N/A')
            category = p.get('category') or p.get('type', 'General')
            description = p.get('description', '')[:100]
            product_id = p.get('id', 'N/A')
            
            formatted.append(
                f"{i}. {name} (ID: {product_id}) | Category: {category} | Price: {price} | {description}"
            )
        return "\n".join(formatted)


class ConversationalCrew:
    def __init__(self, agents, products_json_path: str = "rproducts.json"):
        self.agents = agents
        self.product_rag = ProductRAGWithEmbeddings(products_json_path)
        
        # Initialize embeddings at startup (one-time preprocessing)
        print("\n" + "="*60)
        print("INITIALIZING RAG SYSTEM")
        print("="*60)
        self.product_rag.generate_embeddings()
        print("="*60 + "\n")
        
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
                            "product_ids": genai.protos.Schema(
                                type=genai.protos.Type.ARRAY,
                                description="IDs of products being recommended or mentioned",
                                items=genai.protos.Schema(type=genai.protos.Type.NUMBER)
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
        """
        Get relevant products using RAG (with embeddings)
        This now uses fast vector similarity instead of LLM inference
        """
        recommendation_keywords = [
            'recommend', 'suggest', 'looking for', 'need', 'want', 
            'show me', 'find', 'search', 'buy', 'purchase', 'get'
        ]
        
        user_input_lower = user_input.lower()
        is_recommendation_query = any(keyword in user_input_lower for keyword in recommendation_keywords)
        
        if is_recommendation_query:
            # Use embedding-based search (FAST!)
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
        
        # Get RAG context using embedding-based retrieval
        rag_context = self._get_rag_context(user_input)
        
        # Create comprehensive prompt
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

RELEVANT PRODUCTS (retrieved using embedding similarity):
{rag_context}

USER MESSAGE: {user_input}

Instructions:
1. Choose the most appropriate agent based on the user's intent
2. If this is a recommendation/product query, USE THE RELEVANT PRODUCTS listed above
3. Generate a helpful, personalized response as that agent
4. Extract product IDs from the database above and include them in the product_ids array
5. Extract any relevant data (cart items, products, issues, etc.)
6. Stay in character for the chosen agent
7. When recommending products, reference the specific products from the database above
8. ALWAYS include product IDs in the product_ids field when mentioning products
9. End with a question or call to action to keep the conversation going
10. Acknowledge the user's preferences and history
11. If the product is not in the database, apologize and suggest alternatives
12. Make the user flow through the entire shopping process from greeting to purchase
13. Purchase is not completed without payment
14. If a product is not available, apologize and ask if the user would like to see some suggested items (suggest alternatives in the category ).
"""
        
        try:
            # Single LLM call with function calling
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
                    
                    # Extract product IDs
                    product_ids = []
                    if "product_ids" in function_args:
                        product_ids = [int(pid) for pid in list(function_args["product_ids"])]
                    
                    # Extract and update context data
                    if "cart_items" in function_args:
                        new_items = list(function_args["cart_items"])
                        self.context["cart_items"].extend(new_items)
                    
                    if "products_mentioned" in function_args:
                        new_products = list(function_args["products_mentioned"])
                        self.context["products_mentioned"].extend(new_products)
                        if agent_name == "Recommendation Agent":
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
                        "product_ids": product_ids,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    return agent_name, reply, product_ids
                
                elif part.text:
                    text_response = part.text
                    self.context["conversation_history"].append({
                        "user": user_input,
                        "agent": "General Assistant",
                        "reply": text_response,
                        "product_ids": [],
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    return "General Assistant", text_response, []
            
            raise ValueError("No valid response from model")
                
        except Exception as e:
            import traceback
            error_msg = f"I apologize, I encountered an error: {str(e)}"
            print(f"\nDebug - Full error:\n{traceback.format_exc()}")
            return "Error Handler", error_msg, []
    
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
            "total_products_in_db": len(self.product_rag.products),
            "embeddings_ready": self.product_rag.embeddings_generated
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
        role="Recommendation Agent",
        goal="Analyze items available in the store and make personalized recommendations based on product database.",
        backstory="Expert in product analytics with access to comprehensive product database. Uses data-driven insights to match customers with perfect products. " \
        "Start showing relevant products from the database the moment a user expresses interest. ALWAYS include product IDs.",
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
        backstory="Experienced in e-commerce and user experience. Check inventory before adding items to cart.",
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


# Create the conversational crew with embedding-based RAG
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
    products_json_path="rproducts.json"
)

print("\n### CrewAI with Embedding-Based RAG ###")
print(f"✓ System ready with {len(crew.product_rag.products)} products")
print("Type 'exit' to quit, 'summary' to see context summary.\n")