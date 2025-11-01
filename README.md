# CrewAI E-Commerce Chatbot 🛍️🤖

An intelligent, multi-agent conversational chatbot system for e-commerce platforms built with CrewAI, FastAPI, and Google's Gemini AI. The system features RAG (Retrieval-Augmented Generation) for personalized product recommendations and seamless customer service automation.

## 🌟 Features

### Multi-Agent System
The chatbot employs 10 specialized AI agents, each handling specific aspects of the e-commerce experience:

- **Sales Specialist**: Drives sales through upselling and cross-selling strategies
- **Recommendation Agent**: Provides personalized product recommendations using RAG
- **Inventory Specialist**: Manages stock availability and inventory queries
- **Shopping Cart Specialist**: Handles cart operations and product additions
- **Logistics Coordinator**: Manages shipping and delivery information
- **Financial Transactions Expert**: Processes payments and handles billing
- **Customer Relations Specialist**: Manages post-purchase support and follow-ups
- **Customer Loyalty Specialist**: Handles loyalty programs and special offers
- **CRM Manager**: Maintains customer relationship data and preferences
- **Technical Support Specialist**: Resolves technical issues and errors

### RAG-Enhanced Product Search
- Semantic search using Google Gemini embeddings
- Intelligent product matching based on user queries
- Fallback keyword search for reliability
- Real-time product database integration

### Conversational Context Management
- Tracks conversation history
- Maintains shopping cart state
- Monitors user preferences and behavior
- Records loyalty points and transactions
- Stores customer information across sessions

### Real-Time WebSocket Communication
- Instant message delivery via WebSocket
- Live agent routing and responses
- Seamless user experience with no page reloads

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │ WebSocket
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ ConversationalCrew│◄───►│  ProductRAG  │
│   (Orchestrator)  │     │   System     │
└────────┬────────┘      └──────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐      ┌──────────────┐
│  10 Specialized │      │   Product    │
│     Agents      │      │   Database   │
└─────────────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  Gemini 2.5     │
│  Flash Lite     │
└─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Cloud API Key (for Gemini AI)
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd crewai-ecommerce-chatbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

Required packages:
- `fastapi`
- `uvicorn[standard]`
- `websockets`
- `crewai`
- `google-generativeai`
- `python-dotenv`
- `jinja2`
- `numpy`

3. **Set up environment variables**

Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

4. **Prepare product database**

Ensure `rproducts.json` is in the `app/` directory with your product catalog. The JSON structure should follow:
```json
{
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "category": "Category",
      "description": "Product description",
      "items": [
        {
          "item_id": "1A",
          "variant": "Color/Size",
          "price": 99.99,
          "description": "Variant details"
        }
      ]
    }
  ]
}
```

### Running the Application

1. **Start the FastAPI server**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Access the chatbot**
Open your browser and navigate to:
```
http://localhost:8000
```

3. **Start chatting!**
The chatbot will automatically route your messages to the appropriate agent and provide intelligent responses.

## 📁 Project Structure

```
crewai-ecommerce-chatbot/
├── app/
│   ├── main.py                 # FastAPI application & WebSocket endpoint
│   ├── crew_backend.py         # Multi-agent system & RAG implementation
│   ├── rproducts.json          # Product database
│   ├── static/
│   │   └── script.js           # Frontend WebSocket client
│   └── templates/
│       ├── index.html          # Main chat interface
│       ├── login.html          # (Placeholder for future auth)
│       └── signup.html         # (Placeholder for future auth)
├── .env                        # Environment variables (create this)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### Customizing Agents

Edit the `MeetingPrepAgents` class in `crew_backend.py` to modify agent behaviors:

```python
Sales_Agent = Agent(
    role="Your Role",
    goal="Your Goal",
    backstory="Your Backstory",
    llm=llm,
    verbose=False
)
```

### Adjusting RAG Settings

Modify RAG parameters in the `ProductRAG` class:

```python
def search_products(self, query: str, top_k: int = 5):
    # Adjust top_k for more/fewer recommendations
    ...
```

### Changing the LLM Model

Update the model in `crew_backend.py`:

```python
llm = LLM(
    model="gemini/gemini-2.5-flash-lite",  # Change model here
    api_key=os.getenv("GOOGLE_API_KEY")
)
```

## 🎯 Usage Examples

### Product Recommendations
```
User: "I'm looking for winter clothing"
Bot: 🧠 Recommendation Agent: Based on our winter collection, I recommend...
```

### Adding to Cart
```
User: "Add the wool overcoat to my cart"
Bot: 🧠 Shopping Cart Specialist: I've added the Wool Overcoat to your cart...
```

### Checking Session Summary
```
User: "summary"
Bot: 📊 Session Summary: {interaction_count, cart_items, loyalty_points...}
```

## 🛠️ API Endpoints

### WebSocket
- **Endpoint**: `/ws`
- **Purpose**: Real-time bidirectional communication
- **Usage**: Connects automatically when opening the chat interface

### REST APIs
- **GET** `/` - Renders the main chat interface
- **GET** `/summary` - Returns session context summary

## 🔐 Security Considerations

- Store API keys securely in `.env` file
- Never commit `.env` to version control
- Implement authentication for production use (login/signup templates provided)
- Validate and sanitize all user inputs
- Use HTTPS in production environments

## 🚧 Future Enhancements

- [ ] User authentication and persistent sessions
- [ ] Payment gateway integration
- [ ] Order tracking system
- [ ] Multi-language support
- [ ] Voice input/output capabilities
- [ ] Analytics dashboard
- [ ] Email notifications
- [ ] Mobile app integration
- [ ] Vector database for improved RAG performance
- [ ] A/B testing for agent responses

## 🐛 Troubleshooting

### WebSocket Connection Failed
- Ensure the server is running on the correct port
- Check firewall settings
- Verify `ws://` protocol in browser console

### Agent Not Responding
- Verify `GOOGLE_API_KEY` is set correctly
- Check API quota limits
- Review console logs for error messages

### Products Not Loading
- Ensure `rproducts.json` is in the correct directory
- Validate JSON structure
- Check file permissions

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Support

For questions or issues, please open an issue on the GitHub repository or contact the maintainers.

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent orchestration framework
- **Google Gemini** - Advanced AI language model
- **FastAPI** - Modern web framework for building APIs
- **Tailwind CSS** - Utility-first CSS framework

---

**Built using CrewAI and Google Gemini**