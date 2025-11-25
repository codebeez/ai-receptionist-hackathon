# AI Receptionist Hackathon

Welcome to the AI Receptionist Hackathon! This project provides a hotel management API with a web interface. Your goal is to build an intelligent chatbot receptionist that can help guests create, update, and cancel hotel bookings using natural conversation.

## 🎯 Hackathon Goal

Build a conversational AI receptionist that uses **OpenAI's LLM with function calling (tools)** to interact with the hotel booking system. The receptionist should understand natural language requests and execute the appropriate API calls to:

- 🏨 Check room availability
- ✅ Create new bookings
- 📝 Update existing bookings
- ❌ Cancel bookings
- 📊 Retrieve booking information

All your code will go in the **`receptionist/`** folder. The hotel API and frontend are already implemented and ready to use!

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
uv sync
```

### Running the Application

```bash
uv run uvicorn main:app --log-level error --port 8000 --reload
```

* The chat interface will be available at http://localhost:8000
* The Swagger UI will be available at http://localhost:8000/docs

## 📁 Project Structure

```
ai_receptionist_hackathon/
├── receptionist/         # Receptionist chatbot code
|   ├── service.py        # 👈 Your implementation goes here
│   └── routes.py         # Chatbot Websocket endpoint
├── hotel/                # Hotel management system (already implemented)
│   ├── models.py         # Pydantic models for API
│   ├── db_models.py      # SQLAlchemy database models
│   ├── repository.py     # Database operations
│   ├── service.py        # Business logic
│   └── routes.py         # REST API endpoints
├── migrations/           # Database setup
│   └── seed_rooms.py     # Initial room data
├── main.py               # FastAPI application entry point
├── dependencies.py       # FastAPI application dependencies
├── index.html            # Chat UI
└── hotel.db              # SQLite database (auto-created)
```

## 🗄️ Database Migrations

The project uses a simple migration system to initialize and populate the database with data.

### How Migration Works

1. **Automatic Execution:** Migration runs automatically when the application starts (see `main.py`)
2. **Idempotent:** Migration checks if data already exists before inserting, so it can be run multiple times safely
3. **Database:** The file `hotel.db` will be created automatically so you can delete it if you want a fresh database

### Seed Data Migration

The `seed_rooms.py` migration creates the initial room inventory with:
- 3 Single rooms (Floor 1)
- 2 Double rooms (Floor 1)  
- 2 Single rooms (Floor 2)
- 2 Double rooms (Floor 2)
- 2 Suites (Floor 3)
- 2 Deluxe suites (Floor 3)

**Total:** 13 rooms across different types and price points

When the migration runs:
- It checks if each room already exists by room number
- Only creates rooms that don't exist yet
- Skips existing rooms to avoid duplicates
- Logs the number of rooms created and skipped

## 🏗️ Available Hotel API Endpoints

The hotel system provides these REST endpoints that your AI receptionist should utilize:

### Rooms
- `GET /rooms` - List all rooms
- `GET /rooms/{room_id}` - Get specific room details
- `POST /availability` - Check room availability for dates

### Bookings
- `POST /bookings` - Create a new booking
- `GET /bookings/{booking_id}` - Get booking details
- `PUT /bookings/{booking_id}` - Update a booking
- `DELETE /bookings/{booking_id}` - Cancel a booking

### Guests
- `GET /guests/{guest_id}/bookings` - Get all bookings for a guest
- `GET /guests/by-email/{email}` - Find guest by email

For detailed API documentation with request/response schemas, visit http://localhost:8000/docs after starting the server.

## 💬 Receptionist WebSocket Endpoint

Your AI receptionist communicates through a WebSocket connection for real-time chat:

- **Endpoint:** `ws://localhost:8000/receptionist`
- **Protocol:** WebSocket

### Message Format

**Incoming messages (from client):**
```json
{
  "type": "user",
  "message": "User's text message here",
  "timestamp": "2025-11-25T12:34:56.789012"
}
```

**Outgoing messages (to client):**
```json
{
  "type": "bot",
  "message": "Receptionist's response",
  "timestamp": "2025-11-25T12:34:56.789012"
}
```

The WebSocket endpoint:
1. Accepts the connection
2. Sends a welcome message
3. Waits for user messages in JSON format
4. Processes each message through `ReceptionistService.handle_message()`
5. Returns responses in JSON format

Your implementation in `receptionist/service.py` should handle incoming messages and return appropriate responses.

## 💡 Implementation Tips

### OpenAI Function Calling

Your chatbot should use OpenAI's function calling feature (also known as "tools") to:

1. **Define functions** that map to the hotel service
2. **Let the LLM decide** which function to call based on user input
3. **Execute the service methods** when the LLM requests them
4. **Return results** to the LLM for a natural language response

### Example Workflow

```
User: "I'd like to book a deluxe room from Dec 15 to Dec 20"
   ↓
LLM analyzes intent → Needs to check availability first
   ↓
Function call: check_availability(check_in="2025-12-15", check_out="2025-12-20", room_type="deluxe")
   ↓
Your code calls checks availability
   ↓
Return available rooms to LLM
   ↓
LLM: "I found a Deluxe Suite available for $350/night. May I have your contact information to complete the booking?"
   ↓
User provides guest details
   ↓
Function call: create_booking(...)
   ↓
Your code calls creates a booking
   ↓
LLM: "Great! Your booking #123 is confirmed for Dec 15-20 in our Deluxe Suite."
```

## 🎓 Learning Resources

- [OpenAI Python SDK GitHub](https://github.com/openai/openai-python)
- [OpenAI Text Generation Docs](https://platform.openai.com/docs/guides/text)
- [OpenAI Function Calling Docs](https://platform.openai.com/docs/guides/function-calling)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)