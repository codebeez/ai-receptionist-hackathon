import logging
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from dependencies import get_receptionist_service
from receptionist.service import ReceptionistService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/receptionist", tags=["receptionist"])


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    service: ReceptionistService = Depends(get_receptionist_service)
):
    """
    WebSocket endpoint for real-time chat with the receptionist bot.
    
    The client connects to this endpoint to establish a persistent connection
    for chatting with the AI receptionist.
    """
    client_id = id(websocket)
    logger.info("WebSocket connection initiated (client: %s)", client_id)

    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted (client: %s)", client_id)

        # Send initial welcome message
        logger.debug("Sending welcome message to client %s", client_id)
        welcome_response = {
            "type": "bot",
            "message": (
                "Welcome! "
                "You are now chatting with our AI Receptionist Bot. "
                "How can I assist you today?"
            ),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(welcome_response)

        try:
            while True:
                # Wait for messages from the client
                logger.debug("Waiting for message from client %s", client_id)
                data = await websocket.receive_json()
                message = data.get('message', '')
                logger.info("Received message from client %s: %s...", client_id, message[:20])

                logger.debug("Sending response to client %s", client_id)
                response_message = await service.handle_message(message)
                response = {
                    "type": "bot",
                    "message": response_message,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(response)

        except WebSocketDisconnect:
            logger.info("Client disconnected normally (client: %s)", client_id)
        except Exception as e:
            logger.error("Error in websocket communication (client: %s): %s", client_id, e, exc_info=True)
            try:
                await websocket.close()
                logger.debug("WebSocket closed for client %s", client_id)
            except Exception as close_error:
                logger.error("Error closing websocket (client: %s): %s", client_id, close_error)
    except Exception as e:
        logger.error("Error accepting websocket connection (client: %s): %s", client_id, e, exc_info=True)
