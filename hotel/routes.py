import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path

from dependencies import get_hotel_service
from hotel.models import (
    AvailabilityRequest,
    BookingCreate,
    BookingDetailResponse,
    BookingUpdate,
    GuestResponse,
    RoomResponse,
)
from hotel.service import HotelService

logger = logging.getLogger(__name__)
router = APIRouter()


# Room endpoints
@router.get(
    "/rooms",
    response_model=List[RoomResponse],
    tags=["Rooms"],
    summary="List all rooms",
    response_description="List of all available rooms in the hotel"
)
def get_all_rooms(service: HotelService = Depends(get_hotel_service)):
    """
    Retrieve a list of all rooms in the hotel.

    Returns detailed information about each room including:
    - Room number and type
    - Price per night
    - Capacity
    - Description

    **Note:** Rooms are created via database migration, not through the API.
    """
    logger.info("GET /rooms")
    try:
        rooms = service.get_all_rooms()
        return rooms
    except Exception as e:
        logger.error("Error retrieving all rooms: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/rooms/{room_id}",
    response_model=RoomResponse,
    tags=["Rooms"],
    summary="Get room by ID",
    response_description="Detailed information about the room"
)
def get_room(
    room_id: int = Path(..., description="Unique identifier of the room", gt=0),
    service: HotelService = Depends(get_hotel_service)
):
    """
    Retrieve detailed information about a specific room by its ID.

    - **room_id**: The unique identifier of the room (must be positive)

    Returns:
    - Room details including number, type, price, capacity, and description

    Raises:
    - **404**: Room not found
    """
    logger.info("GET /rooms/%s", room_id)
    try:
        room = service.get_room(room_id)
        if not room:
            logger.error("Room not found: %s", room_id)
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        return room
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving room %s: %s", room_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


# Availability endpoint
@router.post(
    "/availability",
    response_model=List[RoomResponse],
    tags=["Availability"],
    summary="Check room availability",
    response_description="List of available rooms matching the criteria"
)
def check_availability(
    request: AvailabilityRequest,
    service: HotelService = Depends(get_hotel_service)
):
    """
    Check which rooms are available for a specific date range.

    You can filter results by:
    - **check_in**: Start date of the stay (required)
    - **check_out**: End date of the stay (required)
    - **room_type**: Filter by room type (optional)
    - **capacity**: Minimum capacity required (optional)

    Returns:
    - List of available rooms that match your criteria

    Business Rules:
    - Check-in date must be in the future
    - Check-out date must be after check-in date
    - Only confirmed bookings are considered for availability

    Raises:
    - **400**: Invalid dates or parameters
    - **500**: Server error
    """
    logger.info("POST /availability")
    try:
        rooms = service.check_availability(request)
        return rooms
    except ValueError as e:
        logger.error("Validation error checking availability: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error checking availability: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# Booking endpoints
@router.post(
    "/bookings",
    response_model=BookingDetailResponse,
    status_code=201,
    tags=["Bookings"],
    summary="Create a new booking",
    response_description="Details of the created booking"
)
def create_booking(
    booking_data: BookingCreate,
    service: HotelService = Depends(get_hotel_service)
):
    """
    Create a new booking for a guest.

    Required information:
    - **room_id**: ID of the room to book
    - **guest**: Guest details (first name, last name, email, phone)
    - **check_in**: Check-in date and time
    - **check_out**: Check-out date and time

    The system will:
    - Verify room availability
    - Create or retrieve guest by email
    - Calculate total price automatically
    - Create the booking

    Returns:
    - Complete booking details including room and guest information

    Business Rules:
    - Check-in must be in the future
    - Check-out must be after check-in
    - Room must be available for the selected dates
    - Price is calculated: (nights × room price per night)

    Raises:
    - **400**: Invalid data or room not available
    - **500**: Server error
    """
    logger.info("POST /bookings")
    try:
        booking = service.create_booking(booking_data)
        return booking
    except ValueError as e:
        logger.error("Validation error creating booking: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error creating booking: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingDetailResponse,
    tags=["Bookings"],
    summary="Get booking details",
    response_description="Complete booking information"
)
def get_booking(
    booking_id: int = Path(..., description="Unique identifier of the booking", gt=0),
    service: HotelService = Depends(get_hotel_service)
):
    """
    Retrieve complete details of a specific booking.

    - **booking_id**: The unique identifier of the booking

    Returns:
    - Full booking details including room and guest information
    - Current booking status (confirmed, cancelled, completed)
    - Total price and dates

    Raises:
    - **404**: Booking not found
    """
    logger.info("GET /bookings/%s", booking_id)
    try:
        booking = service.get_booking(booking_id)
        if not booking:
            logger.error("Booking not found: %s", booking_id)
            raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving booking %s: %s", booking_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.put(
    "/bookings/{booking_id}",
    response_model=BookingDetailResponse,
    tags=["Bookings"],
    summary="Update a booking",
    response_description="Updated booking details"
)
def update_booking(
    booking_id: int = Path(..., description="Unique identifier of the booking", gt=0),
    update_data: BookingUpdate = ...,
    service: HotelService = Depends(get_hotel_service)
):
    """
    Update an existing booking's room, dates, or both.

    You can update:
    - **room_id**: Change to a different room (optional)
    - **check_in**: Change check-in date (optional)
    - **check_out**: Change check-out date (optional)

    Features:
    - Update any combination of fields
    - Automatic price recalculation
    - Availability verification for new dates/room

    Business Rules:
    - Only confirmed bookings can be updated
    - Cannot update bookings that have already started
    - New room must be available for new dates
    - System excludes current booking from conflict checks

    Returns:
    - Updated booking with recalculated price

    Raises:
    - **400**: Invalid update data or room not available
    - **404**: Booking not found
    - **500**: Server error
    """
    logger.info("PUT /bookings/%s", booking_id)
    try:
        booking = service.update_booking(booking_id, update_data)
        return booking
    except ValueError as e:
        logger.error("Validation error updating booking %s: %s", booking_id, e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error updating booking %s: %s", booking_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/bookings/{booking_id}",
    response_model=BookingDetailResponse,
    tags=["Bookings"],
    summary="Cancel a booking",
    response_description="Cancelled booking details"
)
def cancel_booking(
    booking_id: int = Path(..., description="Unique identifier of the booking", gt=0),
    service: HotelService = Depends(get_hotel_service)
):
    """
    Cancel an existing booking.

    - **booking_id**: The unique identifier of the booking to cancel

    Business Rules:
    - Only confirmed bookings can be cancelled
    - Cannot cancel bookings that have already started
    - Cannot cancel already cancelled or completed bookings

    Returns:
    - Booking details with status changed to "cancelled"
    - Cancellation timestamp

    Raises:
    - **400**: Cannot cancel (already started, wrong status, etc.)
    - **404**: Booking not found
    - **500**: Server error
    """
    logger.info("DELETE /bookings/%s", booking_id)
    try:
        booking = service.cancel_booking(booking_id)
        return booking
    except ValueError as e:
        logger.error("Validation error cancelling booking %s: %s", booking_id, e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error cancelling booking %s: %s", booking_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# Guest endpoints
@router.get(
    "/guests/{guest_id}/bookings",
    response_model=List[BookingDetailResponse],
    tags=["Guests"],
    summary="Get guest's bookings",
    response_description="List of all bookings for the guest"
)
def get_guest_bookings(
    guest_id: int = Path(..., description="Unique identifier of the guest", gt=0),
    service: HotelService = Depends(get_hotel_service)
):
    """
    Retrieve all bookings for a specific guest.

    - **guest_id**: The unique identifier of the guest

    Returns:
    - List of all bookings (past and current) for this guest
    - Each booking includes full room and guest details
    - Bookings of all statuses (confirmed, cancelled, completed)

    Useful for:
    - Viewing guest booking history
    - Checking current reservations
    - Analyzing guest patterns
    """
    logger.info("GET /guests/%s/bookings", guest_id)
    try:
        bookings = service.get_guest_bookings(guest_id)
        return bookings
    except Exception as e:
        logger.error("Error retrieving bookings for guest %s: %s", guest_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/guests/by-email/{email}",
    response_model=GuestResponse,
    tags=["Guests"],
    summary="Find guest by email",
    response_description="Guest information"
)
def get_guest_by_email(
    email: str = Path(..., description="Email address of the guest"),
    service: HotelService = Depends(get_hotel_service)
):
    """
    Find a guest by their email address.

    - **email**: The email address to search for

    Returns:
    - Guest information including ID, name, contact details
    - Registration date

    Use this to:
    - Look up returning guests
    - Verify guest information
    - Find guest ID for booking queries

    Raises:
    - **404**: Guest with this email not found
    """
    logger.info("GET /guests/by-email/%s", email)
    try:
        guest = service.get_guest_by_email(email)
        if not guest:
            logger.error("Guest not found with email: %s", email)
            raise HTTPException(status_code=404, detail=f"Guest with email {email} not found")
        return guest
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving guest by email %s: %s", email, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e
