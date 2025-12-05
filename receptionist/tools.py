HOTEL_TOOLS = [
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check for available rooms within a specific date range, optionally filtering by room type and capacity.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "check_in": {
                    "type": "string",
                    "description": "Start date of the stay (ISO 8601 format, e.g., '2025-12-01T14:00:00')",
                },
                "check_out": {
                    "type": "string",
                    "description": "End date of the stay (ISO 8601 format, e.g., '2025-12-05T11:00:00')",
                },
                "room_type": {
                    "type": ["string", "null"],
                    "enum": ["single", "double", "suite", "deluxe"],
                    "description": "Filter by room type. Pass null if no specific preference.",
                },
                "capacity": {
                    "type": ["integer", "null"],
                    "description": "Minimum person capacity required. Pass null if no specific preference.",
                },
            },
            "required": ["check_in", "check_out", "room_type", "capacity"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_booking",
        "description": "Create a new booking for a specific room and guest.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": "integer",
                    "description": "The unique ID of the room to book.",
                },
                "check_in": {"type": "string", "description": "Check-in date (ISO 8601 format)."},
                "check_out": {
                    "type": "string",
                    "description": "Check-out date (ISO 8601 format).",
                },
                "guest_first_name": {"type": "string", "description": "Guest's first name."},
                "guest_last_name": {"type": "string", "description": "Guest's last name."},
                "guest_email": {"type": "string", "description": "Guest's email address."},
                "guest_phone": {"type": "string", "description": "Guest's phone number."},
            },
            "required": [
                "room_id",
                "check_in",
                "check_out",
                "guest_first_name",
                "guest_last_name",
                "guest_email",
                "guest_phone",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "update_booking",
        "description": "Update an existing booking's dates or room assignment.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "integer",
                    "description": "The ID of the booking to update.",
                },
                "room_id": {
                    "type": ["integer", "null"],
                    "description": "New room ID. Pass null to keep the current room.",
                },
                "check_in": {
                    "type": ["string", "null"],
                    "description": "New check-in date. Pass null to keep current date.",
                },
                "check_out": {
                    "type": ["string", "null"],
                    "description": "New check-out date. Pass null to keep current date.",
                },
            },
            "required": ["booking_id", "room_id", "check_in", "check_out"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "cancel_booking",
        "description": "Cancel an existing booking by ID.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "integer",
                    "description": "The ID of the booking to cancel.",
                }
            },
            "required": ["booking_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_room_details",
        "description": "Get details for a specific room or all rooms.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": ["integer", "null"],
                    "description": "The ID of the room to retrieve. Pass null to list all rooms.",
                }
            },
            "required": ["room_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_my_bookings",
        "description": "Retrieve all bookings associated with a specific guest email.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The email address of the guest."}
            },
            "required": ["email"],
            "additionalProperties": False,
        },
    },
]
