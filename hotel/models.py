from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from hotel.db_models import BookingStatus, RoomType


class RoomBase(BaseModel):
    room_number: str
    room_type: RoomType
    price_per_night: float = Field(gt=0)
    capacity: int = Field(gt=0)
    description: Optional[str] = None


class RoomResponse(RoomBase):
    id: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "room_number": "101",
                    "room_type": "single",
                    "price_per_night": 100.0,
                    "capacity": 1,
                    "description": "Cozy single room with city view"
                }
            ]
        }
    }


class GuestBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Guest's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Guest's last name")
    email: str = Field(..., description="Guest's email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Guest's phone number")


class GuestCreate(GuestBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890"
                }
            ]
        }
    }


class GuestResponse(GuestBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "created_at": "2025-11-24T10:00:00"
                }
            ]
        }
    }


class BookingCreate(BaseModel):
    room_id: int = Field(..., gt=0, description="ID of the room to book")
    guest: GuestCreate
    check_in: datetime = Field(..., description="Check-in date and time")
    check_out: datetime = Field(..., description="Check-out date and time")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "room_id": 1,
                    "guest": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890"
                    },
                    "check_in": "2025-12-01T14:00:00",
                    "check_out": "2025-12-05T11:00:00"
                }
            ]
        }
    }


class BookingUpdate(BaseModel):
    room_id: Optional[int] = Field(None, gt=0, description="New room ID (optional)")
    check_in: Optional[datetime] = Field(None, description="New check-in date (optional)")
    check_out: Optional[datetime] = Field(None, description="New check-out date (optional)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "room_id": 2,
                    "check_in": "2025-12-10T14:00:00",
                    "check_out": "2025-12-15T11:00:00"
                }
            ]
        }
    }


class BookingResponse(BaseModel):
    id: int
    room_id: int
    guest_id: int
    check_in: datetime
    check_out: datetime
    status: BookingStatus
    total_price: float
    created_at: datetime
    cancelled_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "room_id": 1,
                    "guest_id": 1,
                    "check_in": "2025-12-01T14:00:00",
                    "check_out": "2025-12-05T11:00:00",
                    "status": "confirmed",
                    "total_price": 400.0,
                    "created_at": "2025-11-24T10:00:00",
                    "cancelled_at": None
                }
            ]
        }
    }


class BookingDetailResponse(BookingResponse):
    room: RoomResponse
    guest: GuestResponse

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "room_id": 1,
                    "guest_id": 1,
                    "check_in": "2025-12-01T14:00:00",
                    "check_out": "2025-12-05T11:00:00",
                    "status": "confirmed",
                    "total_price": 400.0,
                    "created_at": "2025-11-24T10:00:00",
                    "cancelled_at": None,
                    "room": {
                        "id": 1,
                        "room_number": "101",
                        "room_type": "single",
                        "price_per_night": 100.0,
                        "capacity": 1,
                        "description": "Cozy single room with city view"
                    },
                    "guest": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890",
                        "created_at": "2025-11-24T09:30:00"
                    }
                }
            ]
        }
    }


class AvailabilityRequest(BaseModel):
    check_in: datetime = Field(..., description="Start date of the stay")
    check_out: datetime = Field(..., description="End date of the stay")
    room_type: Optional[RoomType] = Field(None, description="Filter by room type (optional)")
    capacity: Optional[int] = Field(None, gt=0, description="Minimum capacity required (optional)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "check_in": "2025-12-01T14:00:00",
                    "check_out": "2025-12-05T11:00:00",
                    "room_type": "single",
                    "capacity": 1
                }
            ]
        }
    }
