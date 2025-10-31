from crewai import Agent, Task, Crew
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
model = genai.GenerativeModel('gemini-2.5-flash-lite')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



class ConversationalCrew:
    def __init__(self, agents):
        self.agents = agents
        self.context = []  # memory of conversation
        self.client = model  # or whatever LLM backend CrewAI uses
        self.meta_prompt = """
        You are the orchestrator of a multi-agent team.
        Given the user's latest message and the context so far,
        decide which agent should respond next.
        Output in JSON: {"chosen_agent": "<agent name>", "reason": "<why>"}
        """

    def decide_agent(self, user_input):
        context_summary = "\n".join(
            [f"User: {m['user']}\n{m['agent']}: {m['reply']}" for m in self.context[-5:]]
        )
        system_prompt = self.meta_prompt + f"""
        Agents available: {[a.role for a in self.agents]}
        Context:\n{context_summary}
        New message: {user_input}
        """
        response = self.client.generate_content(
        
            contents=[
                {"role": "system", "content": "You are a reasoning orchestrator."},
                {"role": "user", "content": system_prompt}
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
            )
        )
        result = response.choices[0].message.content
        # parse JSON (safe parsing omitted here)
        chosen_name = result.split('"chosen_agent": "')[1].split('"')[0]
        return next(a for a in self.agents if a.role.lower() == chosen_name.lower())

    def route_message(self, user_input):
        """Decide which agent should reply and get their response."""
        agent = self.decide_agent(user_input)
        reply = self.agent_think(agent, user_input)
        self.context.append({"user": user_input, "agent": agent.role, "reply": reply})
        return agent.role, reply

    def agent_think(self, agent, user_input):
        """LLM reasoning for the selected agent."""
        context_text = "\n".join(
            [f"User: {m['user']}\n{m['agent']}: {m['reply']}" for m in self.context[-5:]]
        )
        prompt = f"""
        You are {agent.role}, a {agent.role}.
        Goal: {agent.goal}
        Context:\n{context_text}
        User says: {user_input}
        Reply in first-person tone.
        """
        response = self.client.generate_content(
        
            contents=[
                {"role": "system", "content": f"You are {agent.role}."},
                {"role": "user", "content": prompt}
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.7
            )
        )
        return response.choices[0].message.content
    

class MeetingPrepAgents:
    Sales_Agent = Agent(
        role="Sales Specialist",
        goal="Drive sales and meet performance targets by upselling and cross selling products.",
        backstory="Experienced in sales strategies and customer engagement. Subtly influences customer decisions to maximize revenue.",
        llm=model
    )
    Recommendation_Agent = Agent(
        role="Data Analyst",
        goal="Analyze items available in the store and make recommendations.",
        backstory="Expert in sales and the metrics of related products.",
        llm=model
    )

    Inventory_Agent = Agent(
        role="Inventory Specialist",
        goal="Manage inventory levels and stock availability.",
        backstory="Detail-oriented and experienced in inventory management.",
        llm=model
    )

    Cart_Agent = Agent(
        role="Shopping Cart Specialist",
        goal="Manage shopping cart operations and user interactions.",
        backstory="Experienced in e-commerce and user experience.",
        llm=model
    )

    Fulfillment_Agent = Agent(
        role="Logistics Coordinator",
        goal="Coordinate logistics and ensure timely delivery of items.",
        backstory="Detail-oriented and efficient in managing supply chains.",
        llm=model
    )

    Payment_Agent = Agent(
        role="Financial Transactions Expert",
        goal="Handle payment processing and financial records.",
        backstory="Skilled in secure and efficient payment systems.",  
        llm=model
    )

    Post_Purchase_Agent = Agent(
        role="Customer Relations Specialist",
        goal="Manage post-purchase follow-ups and customer satisfaction.",
        backstory="Focused on building strong customer relationships.",
        llm=model
    )
    
    Loyalty_and_Offers_Agent = Agent(

        role="Customer Loyalty Specialist",
        goal="Manage customer loyalty programs and special offers.",
        backstory="Expert in enhancing customer retention through rewards.",
        llm=model
    )

    CRM_Agent = Agent(
        role="Customer Relationship Manager",
        goal="Maintain and update customer relationship management systems.",
        backstory="Proficient in CRM tools and customer data analysis.",
        llm=model
    )

    Error_Handling_Agent = Agent(
        role="Technical Support Specialist",
        goal="Identify and resolve technical issues in the shopping process.",
        backstory="Experienced in troubleshooting and customer support.",
        llm=model
    ) 
    

    
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

        agent_name, reply = crew.route_message(user_input)
        print(f"{agent_name}: {reply}\n")