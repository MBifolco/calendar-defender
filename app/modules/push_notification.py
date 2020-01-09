from aiohttp import web
from google.cloud import logging
import asyncio
import aiohttp
import os
import modules.token as token


logging_client = logging.Client()
log_name = 'calendar-defender-debug'
logger = logging_client.logger(log_name)

# this belongs in a pushed events class
async def get_updated_events(calendar, user):

    calendar_id = calendar.calendar_id
    url = "https://www.googleapis.com/calendar/v3/calendars/" + calendar_id + "/events/"
    headers = {'Authorization' : "Bearer " + await token.get_token(user)} 
    params = {
        "orderBy": "updated",
        "singleEvents": "True",
        "showDeleted": "False",
        "updatedMin" : calendar.last_check
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    response =  await resp.json()
                    return response["items"]
                else:
                    logger.log_text(await resp.text())
    except Exception as e:
        logger.log_text(str(e))