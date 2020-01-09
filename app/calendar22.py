from google.cloud import logging
import asyncio
import aiohttp
import token

async def get_calendars():
    calendar_id = "mdb388@gmail.com"
    url = "https://www.googleapis.com/calendar/v3/calendars/"
    headers = {'Authorization' : "Bearer " + await token.get_fresh_token()} 
