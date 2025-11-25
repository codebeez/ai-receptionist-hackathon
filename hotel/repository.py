import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, create_engine, or_
from sqlalchemy.orm import Session, joinedload, sessionmaker

from hotel.db_models import Base, Booking, BookingStatus, Guest, Room, RoomType

logger = logging.getLogger(__name__)


class HotelRepository:
    def __init__(self):
        database_url = "sqlite:///./hotel.db"
        logger.debug("Initializing hotel repository with database: %s", database_url)
        try:
            self.engine = create_engine(
                database_url, connect_args={"check_same_thread": False}
            )
            Base.metadata.create_all(bind=self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.debug("Database connection established")
        except Exception as e:
            logger.error("Failed to establish database connection: %s", e, exc_info=True)
            raise

    def get_session(self) -> Session:
        """Get a database session"""
        logger.debug("Creating new database session")
        return self.SessionLocal()

    # Room operations
    def create_room(self, room_number: str, room_type: RoomType, price_per_night: float,
                   capacity: int, description: Optional[str] = None) -> Room:
        """Create a new room"""
        logger.debug("Creating room: %s, type: %s, price: %s", room_number, room_type, price_per_night)
        db = self.get_session()
        try:
            room = Room(
                room_number=room_number,
                room_type=room_type,
                price_per_night=price_per_night,
                capacity=capacity,
                description=description
            )
            db.add(room)
            db.commit()
            db.refresh(room)
            logger.debug("Database: Room created: %s (ID: %s)", room_number, room.id)
            return room
        except Exception as e:
            logger.error("Failed to create room %s: %s", room_number, e, exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def get_room_by_id(self, room_id: int) -> Optional[Room]:
        """Get a room by ID"""
        logger.debug("Fetching room by ID: %s", room_id)
        db = self.get_session()
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                logger.debug("Room found: %s", room.room_number)
            else:
                logger.debug("Room not found with ID: %s", room_id)
            return room
        except Exception as e:
            logger.error("Error fetching room %s: %s", room_id, e, exc_info=True)
            raise
        finally:
            db.close()

    def get_all_rooms(self) -> List[Room]:
        """Get all rooms"""
        logger.debug("Fetching all rooms")
        db = self.get_session()
        try:
            rooms = db.query(Room).all()
            logger.debug("Retrieved %s rooms", len(rooms))
            return rooms
        except Exception as e:
            logger.error("Error fetching all rooms: %s", e, exc_info=True)
            raise
        finally:
            db.close()

    def get_rooms_by_type(self, room_type: RoomType) -> List[Room]:
        """Get rooms by type"""
        logger.debug("Fetching rooms by type: %s", room_type)
        db = self.get_session()
        try:
            rooms = db.query(Room).filter(Room.room_type == room_type).all()
            logger.debug("Found %s rooms of type %s", len(rooms), room_type)
            return rooms
        except Exception as e:
            logger.error("Error fetching rooms by type %s: %s", room_type, e, exc_info=True)
            raise
        finally:
            db.close()

    # Guest operations
    def create_guest(self, first_name: str, last_name: str, email: str, phone: str) -> Guest:
        """Create a new guest or return existing one by email"""
        logger.debug("Creating/retrieving guest: %s", email)
        db = self.get_session()
        try:
            # Check if guest already exists
            existing_guest = db.query(Guest).filter(Guest.email == email).first()
            if existing_guest:
                logger.debug("Guest already exists with email %s (ID: %s)", email, existing_guest.id)
                return existing_guest

            guest = Guest(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone
            )
            db.add(guest)
            db.commit()
            db.refresh(guest)
            logger.debug("Database: Guest created: %s %s (ID: %s)", first_name, last_name, guest.id)
            return guest
        except Exception as e:
            logger.error("Error creating guest %s: %s", email, e, exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def get_guest_by_id(self, guest_id: int) -> Optional[Guest]:
        """Get a guest by ID"""
        logger.debug("Fetching guest by ID: %s", guest_id)
        db = self.get_session()
        try:
            guest = db.query(Guest).filter(Guest.id == guest_id).first()
            if guest:
                logger.debug("Guest found: %s %s", guest.first_name, guest.last_name)
            else:
                logger.debug("Guest not found with ID: %s", guest_id)
            return guest
        except Exception as e:
            logger.error("Error fetching guest %s: %s", guest_id, e, exc_info=True)
            raise
        finally:
            db.close()

    def get_guest_by_email(self, email: str) -> Optional[Guest]:
        """Get a guest by email"""
        logger.debug("Fetching guest by email: %s", email)
        db = self.get_session()
        try:
            guest = db.query(Guest).filter(Guest.email == email).first()
            if guest:
                logger.debug("Guest found: %s %s (ID: %s)", guest.first_name, guest.last_name, guest.id)
            else:
                logger.debug("Guest not found with email: %s", email)
            return guest
        except Exception as e:
            logger.error("Error fetching guest by email %s: %s", email, e, exc_info=True)
            raise
        finally:
            db.close()

    # Booking operations
    def create_booking(self, room_id: int, guest_id: int, check_in: datetime,
                      check_out: datetime, total_price: float) -> Booking:
        """Create a new booking"""
        logger.debug(
            "Creating booking: room_id=%s, guest_id=%s, check_in=%s, check_out=%s",
            room_id,
            guest_id,
            check_in,
            check_out
        )
        db = self.get_session()
        try:
            booking = Booking(
                room_id=room_id,
                guest_id=guest_id,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                status=BookingStatus.CONFIRMED
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)
            logger.debug("Database: Booking created (ID: %s, total: %.2f)", booking.id, total_price)
            return booking
        except Exception as e:
            logger.error("Failed to create booking for room %s: %s", room_id, e, exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def get_booking_by_id(self, booking_id: int) -> Optional[Booking]:
        """Get a booking by ID with relationships loaded"""
        logger.debug("Fetching booking by ID: %s", booking_id)
        db = self.get_session()
        try:
            booking = db.query(Booking).options(
                joinedload(Booking.room),
                joinedload(Booking.guest)
            ).filter(Booking.id == booking_id).first()

            # Make the object expunged from session so relationships are accessible
            if booking:
                db.expunge_all()
                logger.debug("Booking found: ID=%s, status=%s", booking_id, booking.status)
            else:
                logger.debug("Booking not found with ID: %s", booking_id)
            return booking
        except Exception as e:
            logger.error("Error fetching booking %s: %s", booking_id, e, exc_info=True)
            raise
        finally:
            db.close()

    def cancel_booking(self, booking_id: int) -> Optional[Booking]:
        """Cancel a booking"""
        logger.debug("Cancelling booking: %s", booking_id)
        db = self.get_session()
        try:
            booking = db.query(Booking).options(
                joinedload(Booking.room),
                joinedload(Booking.guest)
            ).filter(Booking.id == booking_id).first()

            if booking and booking.status == BookingStatus.CONFIRMED:
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = datetime.now()
                db.commit()
                db.refresh(booking)
                logger.debug("Database: Booking cancelled (ID: %s)", booking_id)
            elif booking:
                logger.debug("Booking %s has status %s, cannot cancel", booking_id, booking.status)
            else:
                logger.debug("Booking not found with ID: %s", booking_id)

            # Expunge to make relationships accessible after session close
            if booking:
                db.expunge_all()
            return booking
        except Exception as e:
            logger.error("Error cancelling booking %s: %s", booking_id, e, exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def update_booking(self, booking_id: int, room_id: Optional[int] = None,
                      check_in: Optional[datetime] = None,
                      check_out: Optional[datetime] = None,
                      total_price: Optional[float] = None) -> Optional[Booking]:
        """Update a booking's room, dates, or both"""
        logger.debug(
            "Updating booking %s: room_id=%s, check_in=%s, check_out=%s",
            booking_id,
            room_id,
            check_in,
            check_out
        )
        db = self.get_session()
        try:
            booking = db.query(Booking).options(
                joinedload(Booking.room),
                joinedload(Booking.guest)
            ).filter(Booking.id == booking_id).first()

            if not booking:
                logger.debug("Booking not found with ID: %s", booking_id)
                return None

            # Update fields if provided
            updates = []
            if room_id is not None:
                booking.room_id = room_id
                updates.append("room")
            if check_in is not None:
                booking.check_in = check_in
                updates.append("check_in")
            if check_out is not None:
                booking.check_out = check_out
                updates.append("check_out")
            if total_price is not None:
                booking.total_price = total_price
                updates.append("price")

            db.commit()
            db.refresh(booking)
            logger.debug("Database: Booking %s updated: %s", booking_id, ', '.join(updates))

            # Expunge to make relationships accessible after session close
            db.expunge_all()
            return booking
        except Exception as e:
            logger.error("Error updating booking %s: %s", booking_id, e, exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def get_bookings_by_guest(self, guest_id: int) -> List[Booking]:
        """Get all bookings for a guest with relationships loaded"""
        logger.debug("Fetching bookings for guest: %s", guest_id)
        db = self.get_session()
        try:
            bookings = db.query(Booking).options(
                joinedload(Booking.room),
                joinedload(Booking.guest)
            ).filter(Booking.guest_id == guest_id).all()

            # Expunge to make relationships accessible after session close
            db.expunge_all()
            logger.debug("Found %s bookings for guest %s", len(bookings), guest_id)
            return bookings
        except Exception as e:
            logger.error("Error fetching bookings for guest %s: %s", guest_id, e, exc_info=True)
            raise
        finally:
            db.close()

    def get_room_bookings(self, room_id: int, check_in: datetime,
                         check_out: datetime) -> List[Booking]:
        """Get all confirmed bookings for a room in a date range"""
        logger.debug("Checking bookings for room %s between %s and %s", room_id, check_in, check_out)
        db = self.get_session()
        try:
            # Find bookings that overlap with the requested period
            bookings = db.query(Booking).filter(
                and_(
                    Booking.room_id == room_id,
                    Booking.status == BookingStatus.CONFIRMED,
                    or_(
                        # Booking starts during requested period
                        and_(Booking.check_in >= check_in, Booking.check_in < check_out),
                        # Booking ends during requested period
                        and_(Booking.check_out > check_in, Booking.check_out <= check_out),
                        # Booking encompasses entire requested period
                        and_(Booking.check_in <= check_in, Booking.check_out >= check_out)
                    )
                )
            ).all()
            logger.debug("Found %s conflicting bookings for room %s", len(bookings), room_id)
            return bookings
        except Exception as e:
            logger.error("Error fetching room bookings for room %s: %s", room_id, e, exc_info=True)
            raise
        finally:
            db.close()

    def get_available_rooms(self, check_in: datetime, check_out: datetime,
                           room_type: Optional[RoomType] = None,
                           capacity: Optional[int] = None) -> List[Room]:
        """Get all available rooms for a date range with optional filters"""
        logger.debug(
            "Finding available rooms: check_in=%s, check_out=%s, type=%s, capacity=%s",
            check_in,
            check_out,
            room_type,
            capacity
        )
        db = self.get_session()
        try:
            # Start with all rooms
            query = db.query(Room)

            # Apply filters
            if room_type:
                query = query.filter(Room.room_type == room_type)
            if capacity:
                query = query.filter(Room.capacity >= capacity)

            all_rooms = query.all()
            logger.debug("Found %s rooms matching filters", len(all_rooms))

            # Filter out rooms with conflicting bookings
            available_rooms = []
            for room in all_rooms:
                conflicting_bookings = self.get_room_bookings(room.id, check_in, check_out)
                if not conflicting_bookings:
                    available_rooms.append(room)

            logger.debug("After availability check: %s rooms available", len(available_rooms))
            return available_rooms
        except Exception as e:
            logger.error("Error finding available rooms: %s", e, exc_info=True)
            raise
        finally:
            db.close()
