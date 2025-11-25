from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends
from openai import AsyncOpenAI

from hotel.repository import HotelRepository
from hotel.service import HotelService
from receptionist.service import ReceptionistService

load_dotenv()


@lru_cache(maxsize=1)
def get_hotel_repository() -> HotelRepository:
    """Get or create the hotel repository instance"""
    return HotelRepository()


@lru_cache(maxsize=1)
def get_hotel_service(
    repository: HotelRepository = Depends(get_hotel_repository)
) -> HotelService:
    """Get or create the hotel service instance"""
    return HotelService(repository)


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """Get or create the OpenAI client instance"""
    return AsyncOpenAI()


def get_receptionist_service(
    openai_client: AsyncOpenAI = Depends(get_openai_client),
    hotel_service: HotelService = Depends(get_hotel_service)
) -> ReceptionistService:
    """
    Get or create the receptionist service instance.

    This is not a singleton, so each request will create a new instance.
    """
    return ReceptionistService(openai_client, hotel_service)
