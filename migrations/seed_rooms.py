"""
Seed script to populate initial rooms in the database
This is run automatically on application startup
"""
import logging

from hotel.db_models import RoomType
from hotel.repository import HotelRepository

logger = logging.getLogger(__name__)


def seed_rooms():
    """Seed the database with initial rooms"""
    logger.info("Starting room seeding migration")
    repo = HotelRepository()

    # Define the rooms to be created
    rooms_data = [
        # Single Rooms (Floor 1)
        {
            "room_number": "101",
            "room_type": RoomType.SINGLE,
            "price_per_night": 100.0,
            "capacity": 1,
            "description": "Cozy single room with city view"
        },
        {
            "room_number": "102",
            "room_type": RoomType.SINGLE,
            "price_per_night": 100.0,
            "capacity": 1,
            "description": "Comfortable single room with garden view"
        },
        {
            "room_number": "103",
            "room_type": RoomType.SINGLE,
            "price_per_night": 100.0,
            "capacity": 1,
            "description": "Modern single room with balcony"
        },
        # Double Rooms (Floor 1)
        {
            "room_number": "104",
            "room_type": RoomType.DOUBLE,
            "price_per_night": 150.0,
            "capacity": 2,
            "description": "Spacious double room with queen bed"
        },
        {
            "room_number": "105",
            "room_type": RoomType.DOUBLE,
            "price_per_night": 150.0,
            "capacity": 2,
            "description": "Double room with twin beds"
        },
        # Single Rooms (Floor 2)
        {
            "room_number": "201",
            "room_type": RoomType.SINGLE,
            "price_per_night": 120.0,
            "capacity": 1,
            "description": "Premium single room on higher floor"
        },
        {
            "room_number": "202",
            "room_type": RoomType.SINGLE,
            "price_per_night": 120.0,
            "capacity": 1,
            "description": "Executive single room with workspace"
        },
        # Double Rooms (Floor 2)
        {
            "room_number": "203",
            "room_type": RoomType.DOUBLE,
            "price_per_night": 180.0,
            "capacity": 2,
            "description": "Premium double room with city skyline view"
        },
        {
            "room_number": "204",
            "room_type": RoomType.DOUBLE,
            "price_per_night": 180.0,
            "capacity": 2,
            "description": "Deluxe double room with sofa area"
        },
        # Suites (Floor 3)
        {
            "room_number": "301",
            "room_type": RoomType.SUITE,
            "price_per_night": 250.0,
            "capacity": 4,
            "description": "Junior suite with separate living area"
        },
        {
            "room_number": "302",
            "room_type": RoomType.SUITE,
            "price_per_night": 250.0,
            "capacity": 4,
            "description": "Family suite with two bedrooms"
        },
        # Deluxe Suites (Floor 3)
        {
            "room_number": "303",
            "room_type": RoomType.DELUXE,
            "price_per_night": 350.0,
            "capacity": 4,
            "description": "Deluxe suite with panoramic city views"
        },
        {
            "room_number": "304",
            "room_type": RoomType.DELUXE,
            "price_per_night": 350.0,
            "capacity": 4,
            "description": "Presidential suite with luxury amenities"
        },
    ]

    created_count = 0
    skipped_count = 0

    for room_data in rooms_data:
        room_number = room_data.get("room_number", "unknown")
        # Check if room already exists
        existing_rooms = repo.get_all_rooms()
        if any(r.room_number == room_data["room_number"] for r in existing_rooms):
            logger.debug("Room %s already exists, skipping", room_number)
            skipped_count += 1
            continue

        try:
            logger.debug("Creating room %s", room_number)
            repo.create_room(**room_data)
            created_count += 1
        except (ValueError, KeyError) as e:
            # Room creation failed (duplicate, invalid data, etc.)
            # Don't fail the entire migration, just skip this room
            logger.error("Failed to create room %s: %s", room_number, e)
            skipped_count += 1
        except Exception as e:
            logger.error("Unexpected error creating room %s: %s", room_number, e, exc_info=True)
            skipped_count += 1

    if created_count > 0 or skipped_count > 0:
        result_msg = f"Room migration: Created {created_count}, Skipped {skipped_count} rooms"
        logger.info(result_msg)


def run_migrations():
    """Run all migrations - wrapper for easy calling from main app"""
    logger.info("Running all migrations")
    try:
        seed_rooms()
        logger.info("All migrations completed successfully")
    except Exception as e:
        logger.error("Migration failed: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    # Only show detailed output when run manually
    print("=" * 60)
    print("Room Seeding Migration")
    print("=" * 60)
    seed_rooms()
    print("=" * 60)
