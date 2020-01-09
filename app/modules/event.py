from google.cloud import logging
import asyncio
import aiohttp
import base64
import os
import modules.token as token

logging_client = logging.Client()
log_name = 'calendar-defender-debug'
logger = logging_client.logger(log_name)

async def get_self_from_attendees(event):
    for attendee in event["attendees"]:
        if "self" in attendee:
            return attendee


async def get_self_response_status(event):
    if "attendees" in event:
        attendee = await get_self_from_attendees(event)
        if attendee["self"] == True:
            return attendee

async def is_attending(event):
    attendee = await get_self_response_status(event)
    try:
        if attendee["responseStatus"] == "accepted":
            return True
    except:
        return False
    return False

async def is_needs_action(event):
    attendee = await get_self_response_status(event)
    if attendee["responseStatus"] == "needsAction":
        return True
    return False

async def is_organizer(event):
    try:
        if "self" in event["organizer"]:
            if event["organizer"]["self"] == True:
                return True
    except:
        return False
    return False

async def is_busy_during_event(event, calendar, user):
    #can pull below out to a is_busy_during time method
    url = "https://www.googleapis.com/calendar/v3/calendars/calendarId/events"
    
    #GET CALENDAR FROM DB
    params = {
        "calendarId": calendar.calendar_id, 
        "timeMin": event["start"]["dateTime"], 
        "timeMax": event["end"]["dateTime"] 
    }
    headers = {
        'Authorization' : "Bearer " + await token.get_token(user),
        "Content-Type" : "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    response =  await resp.json()
                    for competing_event in response['items']:
                        if (await is_attending(competing_event) or await is_organizer(competing_event)) and competing_event["id"] != event["id"]:
                            return True
                    return False
                else:
                    logger.log_text(await resp.text())
                    return False
    except:
        logger.log_text(str(e))
        return False

async def decline_meeting(event, user):
    calendar_id = "mdb388@gmail.com"
    url = "https://www.googleapis.com/calendar/v3/calendars/" + calendar_id+ "/events/" + event["id"]
    headers = {'Authorization' : "Bearer " + await token.get_token(user)} 
    attendee = await get_self_from_attendees(event)
    attendee["responseStatus"] = "declined"
    attendee["comment"] = "Declined automatically by Calendar Defense - I'm already booked"
    params = {
        "sendUpdates" : "all"
    }
    json = {
        "attendees" : [
            attendee
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, params=params, json=json) as resp:
            if resp.status == 200:
                return True
            else:
                return False