from google.cloud import logging
from models.model import *
import asyncio
import aiohttp
import modules.calendar as calendar
import modules.event as event
import modules.push_notification as push_notification
import modules.token as token
import os
import uuid


logging_client = logging.Client()
log_name = 'calendar-defender-debug'
logger = logging_client.logger(log_name)
logger.log_text("app started")

async def receive_pushed_event(request):
    channel_id = request.headers["X-Goog-Channel-ID"]
    resource_id = request.headers["X-Goog-Resource-ID"]
    logger.log_text("push event received: " + channel_id + " " + resource_id)

    try:
        
        # get record from db by channel_id
        calendar = WatchedCalendar.get(WatchedCalendar.channel_id == channel_id)
        # find user associated with calendar
        user = User.get(User.id==calendar.user_id)
        # get all the changed events since the last time we got a notification
        updated_events = await push_notification.get_updated_events(calendar, user)
        
        # THIS NEEDS TO BE AN EVENT LOOP
        for updated_event in updated_events:            
            if "attendees" in updated_event:
                if await event.is_needs_action(updated_event):
                    busy = await event.is_busy_during_event(updated_event, calendar, user)
                    logger.log_text("checked: " + str(channel_id) + ": " + str(busy))
                    if busy: 
                        reject = await event.decline_meeting(updated_event, user)
                        logger.log_text(updated_event["id"] + " was rejected")
                else:
                    logger.log_text(updated_event["id"] + " you're not tentative")
            else:
                logger.log_text(updated_event["id"] + " is not meeting")

        # Update calendar record wih most recent event that was checked.
        for updated_event in reversed(updated_events) :
            if "updated" in updated_event:
                last_check = updated_event["updated"]
                calendar.last_check = last_check
                calendar.save()
                break

        return aiohttp.web.Response(text="Thanks for letting us know.")

    except Exception as e:
        logger.log_text(str(e))
        return aiohttp.web.HTTPBadRequest()


async def watch_calendar(request):

    request = await request.json()
    url = "https://www.googleapis.com/calendar/v3/calendars/" + request['calendar_id'] + "/events/watch"
    json = {
        "id": str(uuid.uuid1()),
        "type": "webhook",
        "address": "https://defender.calendardefense.com/push_event",
        "params": {
            "ttl": "3153600000000"
        }
    }
    headers = {
        'Authorization' : "Bearer " + await token.get_fresh_token(),
        'Content-Type': "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json) as resp:
                if resp.status == 200:
                    response =  await resp.json()
                    return web.Response(text=str(response))
                else:
                   logger.log_text(await resp.text())
    except Exception as e:
        logger.log_text(str(e))

async def get_auth_link():
    endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id" : os.environ.get('CLIENT_ID'),
        "response_type": "code",
        "redirect_uri": "https%3A%2F%2Fcalendardefense.com",
        "scope": [
            "https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly",
            "https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.events",
            "openid%20email"
        ], 
        "access_type": "offline",
        "include_granted_scopes": "true"
    }
   
    url = ""
    return url

async def index(request):
    message = "I defend calendars"
    return aiohttp.web.Response(text=message)

app = aiohttp.web.Application()
app.add_routes([aiohttp.web.get('/', index)])
app.add_routes([aiohttp.web.post('/push_event', receive_pushed_event)])
app.add_routes([aiohttp.web.get('/get_auth_link', get_auth_link)])
app.add_routes([aiohttp.web.post('/watch_calendar', watch_calendar)])

aiohttp.web.run_app(app)