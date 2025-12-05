import base64
import json
from datetime import date
from queue import Queue

from dateutil.parser import parse
from openai import AsyncOpenAI
from openai.types.responses.response_output_item import ResponseOutputItem

from hotel.models import (
    AvailabilityRequest,
    BookingCreate,
    BookingDetailResponse,
    GuestCreate,
    RoomResponse,
)
from hotel.service import HotelService
from receptionist.tools import HOTEL_TOOLS


class ReceptionistService:
    def __init__(self, openai_client: AsyncOpenAI, hotel_service: HotelService):
        self.openai_client = openai_client
        self.hotel_service = hotel_service

    async def handle_message(self, message: str, history: list[dict[str, str]] = []):
        # TODO: Implement actual chatbot logic
        history.append({"role": "user", "content": message})
        print(history)

        response = await self.openai_client.responses.create(
            model="gpt-4o",
            instructions=f"You are a hotel assistant booking bot, it is today {date.today()}. Talk almost exclusively with puns and be mega cringe. Like intentionally bad. Be like a genz gen alpha worker pls",
            input=history,
            tools=HOTEL_TOOLS,
        )

        process_messages = Queue[ResponseOutputItem]()
        for output in response.output:
            process_messages.put(output)

        require_user_input = False

        while not require_user_input:
            msg = process_messages.get()
            if msg.type == "message":
                require_user_input = True
                msg_text = msg.content[0].text
                history.append({"role": "assistant", "content": msg_text})
                return msg_text

            if msg.type == "function_call":
                history.append(msg)
                match msg.name:
                    case "check_availability":
                        request = AvailabilityRequest(**json.loads(msg.arguments))
                        availability: list[RoomResponse] = self.hotel_service.check_availability(
                            request
                        )
                        history.append(
                            {
                                "type": "function_call_output",
                                "call_id": msg.call_id,
                                "output": json.dumps(
                                    {
                                        "check_availability": [
                                            room.model_dump() for room in availability
                                        ]
                                    }
                                ),
                            }
                        )
                    case "create_booking":
                        data = json.loads(msg.arguments)
                        guest_data = GuestCreate(
                            first_name=data["guest_first_name"],
                            last_name=data["guest_last_name"],
                            email=data["guest_email"],
                            phone=data["guest_phone"],
                        )
                        create = BookingCreate(
                            room_id=data["room_id"],
                            check_in=parse(data["check_in"]),
                            check_out=parse(data["check_out"]),
                            guest=guest_data,
                        )
                        booking_detail: BookingDetailResponse = self.hotel_service.create_booking(
                            create
                        )
                        history.append(
                            {
                                "type": "function_call_output",
                                "call_id": msg.call_id,
                                "output": json.dumps(
                                    {"create_booking": booking_detail.model_dump()}, default=str
                                ),
                            }
                        )
                    case _:
                        return f"Fatal error beep boop: {msg.name}"
                response = await self.openai_client.responses.create(
                    model="gpt-4o",
                    input=history,
                    tools=HOTEL_TOOLS,
                )
                for output in response.output:
                    process_messages.put(output)

        print(history)

    async def generate_audio(self, text: str) -> str | None:
        """
        Generates audio from text using OpenAI TTS and returns a Base64 string.
        """
        try:
            response = await self.openai_client.audio.speech.create(
                model="tts-1",  # Low latency model suitable for real-time
                voice="fable",  # "Fable" is great for storytelling/puns
                input=text,
            )

            # OpenAI returns binary content. We need to encode it to Base64
            # so we can send it via JSON over the WebSocket.
            audio_b64 = base64.b64encode(response.content).decode("utf-8")
            return audio_b64
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
