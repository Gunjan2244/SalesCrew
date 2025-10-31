from crewai import Agent, LLM
from dotenv import load_dotenv
import os
import json
import datetime
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.0-flash-exp",
    api_key=os.getenv("GOOGLE_API_KEY")
)


class ConversationalCrew:
    def __init__(self, agents):
        self.agents = agents
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
        
        # Import Gemini directly for function calling
        
        self.genai_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create function declarations for Gemini
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
    
    def route_message(self, user_input):
        """Single LLM call that decides agent AND generates response"""

        
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

USER MESSAGE: {user_input}

Instructions:
1. Choose the most appropriate agent based on the user's intent
2. Generate a helpful, personalized response as that agent
3. Extract any relevant data (cart items, products, issues, etc.)
4. Stay in character for the chosen agent
"""
        
        try:
            # SINGLE LLM CALL with function calling
            response = self.genai_model.generate_content(
                contents=prompt,
                tools=[self.agent_tools],
                tool_config={'function_calling_config': 'AUTO'}
            )
            
            # Extract function call from response
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                agent_function_name = function_call.name
                function_args = dict(function_call.args)
                
                # Get the agent name from function name
                agent_name = agent_function_name.replace("_", " ").title()
                reply = function_args.get("response", "I'm here to help!")
                
                # Extract and update context data
                if function_args.get("cart_items"):
                    new_items = list(function_args["cart_items"])
                    self.context["cart_items"].extend(new_items)
                
                if function_args.get("products_mentioned"):
                    new_products = list(function_args["products_mentioned"])
                    self.context["products_mentioned"].extend(new_products)
                
                if function_args.get("loyalty_points"):
                    self.context["loyalty_points"] = int(function_args["loyalty_points"])
                
                if function_args.get("issue_reported"):
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
            else:
                # Fallback if no function call (shouldn't happen with AUTO mode)
                text_response = response.function_calls[0].text if response.function_call else "I'm here to help!"
                self.context["conversation_history"].append({
                    "user": user_input,
                    "agent": "General Assistant",
                    "reply": text_response,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                return "General Assistant", text_response
                
        except Exception as e:
            error_msg = f"I apologize, I encountered an error: {str(e)}"
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
            "recommendations_made": len(self.context["recommendations_given"])
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
        goal="Analyze items available in the store and make recommendations.",
        backstory="Expert in sales and the metrics of related products.",
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


# Create the conversational crew with single LLM call optimization
crew = ConversationalCrew([
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
])

print("### CrewAI Single-Call Optimization ###")
print("🚀 Each message = 1 LLM call (50% faster, 50% cheaper)")
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