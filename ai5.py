from crewai import Agent, Task, Crew, LLM
from dotenv import load_dotenv
import os
import json

load_dotenv()

# CrewAI's LLM wrapper handles the API structure automatically
llm = LLM(
    model="gemini/gemini-2.0-flash-exp",
    api_key=os.getenv("GOOGLE_API_KEY")
)


class ConversationalCrew:
    def __init__(self, agents):
        self.agents = agents
        self.context = {
            "conversation_history": [],  # Full conversation log
            "user_preferences": {},      # User likes/dislikes, preferences
            "products_mentioned": [],    # Products discussed
            "cart_items": [],            # Items in cart
            "customer_info": {},         # Customer details (name, contact, etc.)
            "issues_reported": [],       # Technical issues or complaints
            "recommendations_given": [], # Product recommendations made
            "transactions": [],          # Payment/order history
            "loyalty_points": 0,         # Loyalty program data
            "follow_ups": [],            # Scheduled follow-ups
            "session_metadata": {        # Session info
                "start_time": None,
                "last_interaction": None,
                "interaction_count": 0
            }
        }
        self.llm = llm
        self.meta_prompt = """
        You are the orchestrator of a multi-agent team.
        Given the user's latest message and the context so far,
        decide which agent should respond next.
        Output in JSON: {"chosen_agent": "<agent name>", "reason": "<why>"}
        """

    def decide_agent(self, user_input):
        context_summary = "\n".join(
            [f"User: {m['user']}\n{m['agent']}: {m['reply']}" for m in self.context["conversation_history"][-5:]]
        )
        
        prompt = self.meta_prompt + f"""
        Agents available: {[a.role for a in self.agents]}
        Context:\n{context_summary}
        New message: {user_input}
        """
        
        # Create a temporary agent for orchestration decisions
        orchestrator = Agent(
            role="Orchestrator",
            goal="Route conversations to the appropriate agent",
            backstory="Expert at understanding user intent and delegating tasks",
            llm=self.llm,
            verbose=False
        )
        
        # Create a task for agent selection
        decision_task = Task(
            description=prompt,
            expected_output="JSON with chosen_agent and reason",
            agent=orchestrator
        )
        
        # Execute the task
        crew = Crew(
            agents=[orchestrator],
            tasks=[decision_task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        # Parse the result
        try:
            result_text = str(result)
            if "{" in result_text and "}" in result_text:
                json_start = result_text.index("{")
                json_end = result_text.rindex("}") + 1
                json_str = result_text[json_start:json_end]
                parsed = json.loads(json_str)
                chosen_name = parsed.get("chosen_agent", "")
            else:
                chosen_name = result_text.split('"chosen_agent": "')[1].split('"')[0]
        except (IndexError, json.JSONDecodeError, ValueError):
            print("Warning: Could not parse agent decision, defaulting to Sales Specialist")
            chosen_name = "Sales Specialist"
        
        # Find matching agent
        for a in self.agents:
            if a.role.lower() == chosen_name.lower():
                return a
        
        return self.agents[0]

    def route_message(self, user_input):
        """Decide which agent should reply and get their response."""
        agent = self.decide_agent(user_input)
        reply = self.agent_think(agent, user_input)
        self.context["conversation_history"].append({"user": user_input, "agent": agent.role, "reply": reply})
        return agent.role, reply

    def agent_think(self, agent, user_input):
        """Let the agent respond using CrewAI's task execution."""
        context_text = "\n".join(
            [f"User: {m['user']}\n{m['agent']}: {m['reply']}" for m in self.context["conversation_history"][-5:]]
        )
        
        prompt = f"""
        Context:\n{context_text}
        
        User says: {user_input}
        
        Reply in first-person tone as your character. Be helpful and stay in character.
        """
        
        # Create a task for the agent's response
        response_task = Task(
            description=prompt,
            expected_output="A helpful response to the user's message",
            agent=agent
        )
        
        # Execute the task
        crew = Crew(
            agents=[agent],
            tasks=[response_task],
            verbose=False
        )
        
        result = crew.kickoff()
        return str(result)
    

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
    

# Create the conversational crew
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

print("### CrewAI Conversational Session Started ###")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    print("Thinking...", end="", flush=True)
    agent_name, reply = crew.route_message(user_input)
    print("\r" + " " * 20 + "\r", end="", flush=True)  # Clear the "Thinking..." line
    print(f"{agent_name}: {reply}\n")