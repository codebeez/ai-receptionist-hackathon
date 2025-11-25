import json
import logging
from datetime import datetime

from openai import AsyncOpenAI

from hotel.service import HotelService
from hotel.models import (
    AvailabilityRequest,
    BookingCreate,
    BookingUpdate,
    GuestCreate,
    RoomType,
)

logger = logging.getLogger(__name__)


class ReceptionistService:
    def __init__(self, openai_client: AsyncOpenAI, hotel_service: HotelService):
        self.openai_client = openai_client
        self.hotel_service = hotel_service

        # Initialize an empty thread
        self.thread = []

    async def handle_message(self, message: str):
        thread = self._get_thread()
        thread.append(
            {
                "role": "user",
                "content": message
            }
        )

        # Initial chat completion
        chat_completion = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=thread,
            tools=self._get_tools(),
            tool_choice="auto"
        )
        thread.append(chat_completion.choices[0].message.model_dump())

        # While there are tool calls, execute them and get the result
        safety_counter = 0
        while chat_completion.choices[0].message.tool_calls and safety_counter < 5:
            safety_counter += 1
            for tool_call in chat_completion.choices[0].message.tool_calls:
                # Execute the tool and get the result
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = self._execute_tool(tool_name, tool_args)

                # Add the tool result to the thread
                thread.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            # Get the next chat completion with tool results
            chat_completion = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=thread,
                tools=self._get_tools(),
                tool_choice="auto"
            )
            thread.append(chat_completion.choices[0].message.model_dump())

        # Return the final chat completion
        return chat_completion.choices[0].message.content

    def _get_thread(self):
        if len(self.thread) == 0:
            self.thread.append(
                {
                    "role": "system",
                    "content": (
                        "You are a receptionist for a hotel. "
                        "You are responsible for helping guests with their bookings and inquiries."
                        "Make sure to verify the guest's identity before helping them "
                        "with any exisiting bookings."
                        "Do not ask users to provide ISO formatted dates, just ask for the date and time in a natural language."
                        "Always generate timezone unaware dates and times."
                    )
                }
            )

        return self.thread

    def _execute_tool(self, tool_name: str, tool_args: dict):
        try:
            match tool_name:
                case "get_room":
                    room = self.hotel_service.get_room(tool_args["room_id"])
                    return room.model_dump_json() if room else "Room not found"
                    # return json.dumps(room.model_dump()) if room else "Room not found"
                case "get_all_rooms":
                    rooms = self.hotel_service.get_all_rooms()
                    return json.dumps([room.model_dump_json() for room in rooms])
                case "check_availability":
                    availability_request = AvailabilityRequest(
                        check_in=datetime.fromisoformat(tool_args["check_in"]),
                        check_out=datetime.fromisoformat(tool_args["check_out"]),
                        room_type=RoomType(tool_args["room_type"]),
                        capacity=int(tool_args["capacity"])
                    )
                    rooms = self.hotel_service.check_availability(availability_request)
                    return json.dumps([room.model_dump_json() for room in rooms])
                case "create_booking":
                    booking_create = BookingCreate(
                        room_id=tool_args["room_id"],
                        check_in=datetime.fromisoformat(tool_args["check_in"]),
                        check_out=datetime.fromisoformat(tool_args["check_out"]),
                        guest=GuestCreate(
                            first_name=tool_args["guest"]["first_name"],
                            last_name=tool_args["guest"]["last_name"],
                            email=tool_args["guest"]["email"],
                            phone=tool_args["guest"]["phone"]
                        )
                    )
                    booking = self.hotel_service.create_booking(booking_create)
                    return booking.model_dump_json() if booking else "Booking not created"
                case "get_booking":
                    booking = self.hotel_service.get_booking(tool_args["booking_id"])
                    return booking.model_dump_json() if booking else "Booking not found"
                case "cancel_booking":
                    booking = self.hotel_service.cancel_booking(tool_args["booking_id"])
                    return booking.model_dump_json() if booking else "Booking not cancelled"
                case "get_guest_bookings":
                    bookings = self.hotel_service.get_guest_bookings(tool_args["guest_id"])
                    return json.dumps([booking.model_dump_json() for booking in bookings])
                case "get_guest_by_email":
                    guest = self.hotel_service.get_guest_by_email(tool_args["email"])
                    return guest.model_dump_json() if guest else "Guest not found"
                case "update_booking":
                    update_booking = BookingUpdate(
                        room_id=tool_args["room_id"],
                        check_in=datetime.fromisoformat(tool_args["check_in"]),
                        check_out=datetime.fromisoformat(tool_args["check_out"])
                    )
                    booking = self.hotel_service.update_booking(
                        booking_id=tool_args["booking_id"],
                        update_data=update_booking
                    )
                    return booking.model_dump_json() if booking else "Booking not updated"
                case _:
                    return "Tool not found"
        except Exception as e:
            logger.error("Error executing tool %s: %s", tool_name, e, exc_info=True)
            return f"Error executing tool {tool_name}: {e}"

    def _get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_room",
                    "description": "Get details about a specific room by its ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_id": {
                                "type": "integer",
                                "description": "The ID of the room to retrieve"
                            }
                        },
                        "required": ["room_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_rooms",
                    "description": "Get a list of all available rooms in the hotel",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": (
                        "Check room availability for a given date range with "
                        "optional filters for room type and capacity"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "check_in": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Check-in date and time (ISO format)"
                            },
                            "check_out": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Check-out date and time (ISO format)"
                            },
                            "room_type": {
                                "type": "string",
                                "description": "Optional filter for room type (e.g., 'single', 'double', 'suite')"
                            },
                            "capacity": {
                                "type": "integer",
                                "description": "Optional filter for minimum room capacity"
                            }
                        },
                        "required": ["check_in", "check_out", "room_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_booking",
                    "description": "Create a new booking for a guest",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_id": {
                                "type": "integer",
                                "description": "The ID of the room to book"
                            },
                            "check_in": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Check-in date and time (ISO format)"
                            },
                            "check_out": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Check-out date and time (ISO format)"
                            },
                            "guest": {
                                "type": "object",
                                "description": "Guest information",
                                "properties": {
                                    "first_name": {
                                        "type": "string",
                                        "description": "Guest's first name"
                                    },
                                    "last_name": {
                                        "type": "string",
                                        "description": "Guest's last name"
                                    },
                                    "email": {
                                        "type": "string",
                                        "description": "Guest's email address"
                                    },
                                    "phone": {
                                        "type": "string",
                                        "description": "Guest's phone number"
                                    }
                                },
                                "required": ["first_name", "last_name", "email", "phone"]
                            }
                        },
                        "required": ["room_id", "check_in", "check_out", "guest"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_booking",
                    "description": "Get details about a specific booking by its ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {
                                "type": "integer",
                                "description": "The ID of the booking to retrieve"
                            }
                        },
                        "required": ["booking_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_booking",
                    "description": (
                        "Cancel an existing booking. "
                        "Cannot cancel bookings that have already started or are completed."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {
                                "type": "integer",
                                "description": "The ID of the booking to cancel"
                            }
                        },
                        "required": ["booking_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_guest_bookings",
                    "description": "Get all bookings for a specific guest by their guest ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guest_id": {
                                "type": "integer",
                                "description": "The ID of the guest"
                            }
                        },
                        "required": ["guest_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_guest_by_email",
                    "description": "Find a guest by their email address to retrieve their guest ID and information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "The email address of the guest"
                            }
                        },
                        "required": ["email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_booking",
                    "description": (
                        "Update an existing booking's room, dates, or both. "
                        "Can only update confirmed bookings that haven't started yet."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {
                                "type": "integer",
                                "description": "The ID of the booking to update"
                            },
                            "room_id": {
                                "type": "integer",
                                "description": "Optional new room ID"
                            },
                            "check_in": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Optional new check-in date and time (ISO format)"
                            },
                            "check_out": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Optional new check-out date and time (ISO format)"
                            }
                        },
                        "required": ["booking_id"]
                    }
                }
            }
        ]
