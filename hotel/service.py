import logging
from datetime import datetime
from typing import List, Optional

from hotel.db_models import BookingStatus
from hotel.models import (
    AvailabilityRequest,
    BookingCreate,
    BookingDetailResponse,
    BookingUpdate,
    GuestResponse,
    RoomResponse,
)
from hotel.repository import HotelRepository

logger = logging.getLogger(__name__)


class HotelService:
    def __init__(self, repository: HotelRepository):
        logger.debug("Initializing HotelService")
        self.repository = repository

    def get_room(self, room_id: int) -> Optional[RoomResponse]:
        """Get a room by ID"""
        logger.debug("Service: Getting room %s", room_id)
        room = self.repository.get_room_by_id(room_id)
        if room:
            return RoomResponse.model_validate(room)
        return None

    def get_all_rooms(self) -> List[RoomResponse]:
        """Get all rooms"""
        logger.debug("Service: Getting all rooms")
        rooms = self.repository.get_all_rooms()
        return [RoomResponse.model_validate(room) for room in rooms]

    def check_availability(self, request: AvailabilityRequest) -> List[RoomResponse]:
        """Check room availability for a given date range"""
        logger.info("Checking availability: %s to %s", request.check_in, request.check_out)
        logger.debug("Availability filters: type=%s, capacity=%s", request.room_type, request.capacity)

        # Validate dates
        try:
            if request.check_in >= request.check_out:
                logger.error("Invalid dates: check-out must be after check-in")
                raise ValueError("Check-out date must be after check-in date")

            if request.check_in < datetime.now():
                logger.error("Invalid dates: check-in cannot be in the past")
                raise ValueError("Check-in date cannot be in the past")

            logger.debug("Date validation passed")
            available_rooms = self.repository.get_available_rooms(
                check_in=request.check_in,
                check_out=request.check_out,
                room_type=request.room_type,
                capacity=request.capacity
            )

            logger.info("Found %s available rooms", len(available_rooms))
            return [RoomResponse.model_validate(room) for room in available_rooms]
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error checking availability: %s", e, exc_info=True)
            raise

    def create_booking(self, booking_data: BookingCreate) -> BookingDetailResponse:
        """Create a new booking"""
        logger.info("Creating booking for room %s", booking_data.room_id)
        logger.debug(
            "Booking details: guest=%s, dates=%s to %s",
            booking_data.guest.email,
            booking_data.check_in,
            booking_data.check_out
        )

        try:
            # Validate dates
            logger.debug("Validating booking dates")
            if booking_data.check_in >= booking_data.check_out:
                logger.error("Invalid dates: check-out must be after check-in")
                raise ValueError("Check-out date must be after check-in date")

            if booking_data.check_in < datetime.now():
                logger.error("Invalid dates: check-in cannot be in the past")
                raise ValueError("Check-in date cannot be in the past")

            # Check if room exists
            logger.debug("Verifying room %s exists", booking_data.room_id)
            room = self.repository.get_room_by_id(booking_data.room_id)
            if not room:
                logger.error("Room not found: %s", booking_data.room_id)
                raise ValueError(f"Room with ID {booking_data.room_id} not found")

            # Check if room is available
            logger.debug("Checking room availability")
            conflicting_bookings = self.repository.get_room_bookings(
                room_id=booking_data.room_id,
                check_in=booking_data.check_in,
                check_out=booking_data.check_out
            )

            if conflicting_bookings:
                logger.error("Room %s not available for selected dates", room.room_number)
                raise ValueError(f"Room {room.room_number} is not available for the selected dates")
            # Create or get guest
            logger.debug("Creating/retrieving guest: %s", booking_data.guest.email)
            guest = self.repository.create_guest(
                first_name=booking_data.guest.first_name,
                last_name=booking_data.guest.last_name,
                email=booking_data.guest.email,
                phone=booking_data.guest.phone
            )

            # Calculate total price
            nights = (booking_data.check_out - booking_data.check_in).days
            total_price = room.price_per_night * nights
            logger.debug("Calculated price: %s nights × $%s = $%s", nights, room.price_per_night, total_price)

            # Create booking
            booking = self.repository.create_booking(
                room_id=booking_data.room_id,
                guest_id=guest.id,
                check_in=booking_data.check_in,
                check_out=booking_data.check_out,
                total_price=total_price
            )

            # Fetch the complete booking with relationships
            booking_with_relations = self.repository.get_booking_by_id(booking.id)
            logger.info("Booking created successfully (ID: %s)", booking.id)
            return BookingDetailResponse.model_validate(booking_with_relations)
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error creating booking: %s", e, exc_info=True)
            raise

    def get_booking(self, booking_id: int) -> Optional[BookingDetailResponse]:
        """Get a booking by ID"""
        logger.debug("Service: Getting booking %s", booking_id)
        booking = self.repository.get_booking_by_id(booking_id)
        if booking:
            return BookingDetailResponse.model_validate(booking)
        return None

    def cancel_booking(self, booking_id: int) -> BookingDetailResponse:
        """Cancel a booking"""
        logger.info("Cancelling booking %s", booking_id)

        try:
            booking = self.repository.get_booking_by_id(booking_id)

            if not booking:
                logger.error("Booking not found: %s", booking_id)
                raise ValueError(f"Booking with ID {booking_id} not found")

            logger.debug("Current booking status: %s", booking.status)

            if booking.status == BookingStatus.CANCELLED:
                logger.error("Booking %s is already cancelled", booking_id)
                raise ValueError(f"Booking {booking_id} is already cancelled")

            if booking.status == BookingStatus.COMPLETED:
                logger.error("Cannot cancel completed booking %s", booking_id)
                raise ValueError(f"Cannot cancel completed booking {booking_id}")

            # Check if booking is in the future
            if booking.check_in < datetime.now():
                logger.error("Cannot cancel booking %s that has already started", booking_id)
                raise ValueError("Cannot cancel a booking that has already started")

            logger.debug("Validation passed, proceeding with cancellation")
            cancelled_booking = self.repository.cancel_booking(booking_id)
            logger.info("Booking %s cancelled successfully", booking_id)
            return BookingDetailResponse.model_validate(cancelled_booking)
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error cancelling booking %s: %s", booking_id, e, exc_info=True)
            raise

    def get_guest_bookings(self, guest_id: int) -> List[BookingDetailResponse]:
        """Get all bookings for a guest"""
        logger.debug("Service: Getting bookings for guest %s", guest_id)
        bookings = self.repository.get_bookings_by_guest(guest_id)
        logger.debug("Found %s bookings for guest %s", len(bookings), guest_id)
        return [BookingDetailResponse.model_validate(booking) for booking in bookings]

    def get_guest_by_email(self, email: str) -> Optional[GuestResponse]:
        """Get a guest by email"""
        logger.debug("Service: Getting guest by email: %s", email)
        guest = self.repository.get_guest_by_email(email)
        if guest:
            return GuestResponse.model_validate(guest)
        return None

    def update_booking(self, booking_id: int, update_data: BookingUpdate) -> BookingDetailResponse:
        """Update a booking's room, dates, or both"""
        logger.info("Updating booking %s", booking_id)
        logger.debug(
            "Update data: room_id=%s, check_in=%s, check_out=%s",
            update_data.room_id,
            update_data.check_in,
            update_data.check_out
        )

        try:
            # Get the current booking
            booking = self.repository.get_booking_by_id(booking_id)

            if not booking:
                logger.error("Booking not found: %s", booking_id)
                raise ValueError(f"Booking with ID {booking_id} not found")

            logger.debug("Current booking status: %s", booking.status)

            if booking.status != BookingStatus.CONFIRMED:
                logger.error("Cannot modify booking %s with status %s", booking_id, booking.status)
                raise ValueError(f"Cannot modify booking {booking_id} with status {booking.status}")

            # Check if booking is in the future
            if booking.check_in < datetime.now():
                logger.error("Cannot modify booking %s that has already started", booking_id)
                raise ValueError("Cannot modify a booking that has already started")

            # Determine the new values (use existing if not provided)
            new_room_id = update_data.room_id if update_data.room_id is not None else booking.room_id
            new_check_in = update_data.check_in if update_data.check_in is not None else booking.check_in
            new_check_out = update_data.check_out if update_data.check_out is not None else booking.check_out

            logger.debug("New values: room=%s, check_in=%s, check_out=%s", new_room_id, new_check_in, new_check_out)

            # Validate new dates
            if new_check_in >= new_check_out:
                logger.error("Invalid dates: check-out must be after check-in")
                raise ValueError("Check-out date must be after check-in date")

            if new_check_in < datetime.now():
                logger.error("Invalid dates: check-in cannot be in the past")
                raise ValueError("Check-in date cannot be in the past")

            # Check if new room exists
            logger.debug("Verifying new room %s exists", new_room_id)
            new_room = self.repository.get_room_by_id(new_room_id)
            if not new_room:
                logger.error("Room not found: %s", new_room_id)
                raise ValueError(f"Room with ID {new_room_id} not found")

            # Check if the new room is available for the new dates
            # Exclude the current booking from the availability check
            logger.debug("Checking availability for new dates/room")
            conflicting_bookings = self.repository.get_room_bookings(
                room_id=new_room_id,
                check_in=new_check_in,
                check_out=new_check_out,
            )

            # Filter out the current booking from conflicts
            conflicting_bookings = [b for b in conflicting_bookings if b.id != booking_id]

            if conflicting_bookings:
                logger.error("Room %s not available for selected dates", new_room.room_number)
                raise ValueError(f"Room {new_room.room_number} is not available for the selected dates")

            # Calculate new total price
            nights = (new_check_out - new_check_in).days
            new_total_price = new_room.price_per_night * nights
            logger.debug(
                "Recalculated price: %s nights × $%s = $%s",
                nights,
                new_room.price_per_night,
                new_total_price,
            )

            # Update the booking
            updated_booking = self.repository.update_booking(
                booking_id=booking_id,
                room_id=new_room_id,
                check_in=new_check_in,
                check_out=new_check_out,
                total_price=new_total_price
            )

            logger.info("Booking %s updated successfully", booking_id)
            return BookingDetailResponse.model_validate(updated_booking)
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error updating booking %s: %s", booking_id, e, exc_info=True)
            raise
