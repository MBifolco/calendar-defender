from aiohttp import web
from models.model import *
import asyncio
import aiohttp
import json
import google.cloud.logging
import logging
import modules.calendar as calendar
from modules.event import Event
from modules.push_notification import PushNotification
import modules.token as token
import os
import urllib.parse
import uuid

client = google.cloud.logging.Client()
client.setup_logging()
logging.info("Now Defending Calendars")

async def receive_pushed_event(request):
    channel_id = request.headers["X-Goog-Channel-ID"]
    logging.info("push event received: " + channel_id)

    try:
        # get which calendar we're watching this is from db by channel_id
        watched_calendar = WatchedCalendar.get(WatchedCalendar.channel_id == channel_id)
        
        # get user associated with calendar
        user = User.get(User.id==watched_calendar.user_id)
        
        # get all the changed events since the last time we got a notification
        push_notification = PushNotification(watched_calendar, user)
        updated_events = await push_notification.get_updated_events()
        #print (updated_events)
        
        # for each event decline it if already busy
        asyncio.gather(*[push_notification.decline_if_busy(updated_event) for updated_event in updated_events],)

        return aiohttp.web.Response(text="Thanks for letting us know.")

    except Exception as e:
        logging.error(str(e), exc_info=True)
        return aiohttp.web.HTTPBadRequest()


async def watch_calendar(request):

    request = await request.json()
    calendars_to_watch = request["calendars_to_watch"]
    user = User.get(User.public_id == request["user_public_id"])

    # this should be an event loop
    for calendar in calendars_to_watch:
        url = "https://www.googleapis.com/calendar/v3/calendars/" + calendar['calendar_id'] + "/events/watch"
        json = {
            "id": str(uuid.uuid1()),
            "type": "webhook",
            "address": "https://defender.calendardefense.com/push_event",
            "params": {
                "ttl": "3153600000000"
            }
        }
        headers = {
            'Authorization' : "Bearer " + await token.get_token(user),
            'Content-Type': "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=json) as resp:
                    if resp.status == 200:
                        response =  await resp.json()
                        #save calendar
                        watched_calendar = WatchedCalendar.get(WatchedCalendar.calendar_id == calendar["calendar_id"])
                        
                        #if we dont' already have it create new
                        if not watched_calendar:
                            watched_calendar =  WatchedCalendar()
                            watched_calendar.public_id = ""
                            watched_calendar.calendar_id = ""
                            watched_calendar.user_id = ""

                        watched_calendar.channel_id = ""
                        watched_calendar.expiration = ""
                        watched_calendar.status = ""
                        watched_calendar.last_check = ""
                        watched_calendar.save()
                        #this should just return a 200
                        return web.Response(text=str(response))
                    else:
                       logging.info(await resp.text())
        except Exception as e:
            logging.info(str(e))

async def get_auth_link(request):
    endpoint = "https://accounts.google.com/o/oauth2/v2/auth?"
    params = {
        "client_id" : os.environ.get('CLIENT_ID'),
        "response_type": "code",
        "redirect_uri": "https://calendardefense.com",
        "scope": " https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events openid email",
        "access_type": "offline",
        "include_granted_scopes": "true"
    }
   
    reponse = {
        "auth_url" : endpoint + urllib.parse.urlencode(params)
    }
    return aiohttp.web.json_response(reponse)

async def swap_auth_code(request):
    request = await request.json()
    auth_code = request["auth_code"]
    
    user = await token.trade_authcode_for_token(auth_code)

    calendar_id_list = calendar.get_list(user)
    
    response = {
        "user" : {
            "public_id" : user.public_id
        },
        "calendar_ids" : calendar_id_list
    }
    return aiohttp.web.json_response(response)

async def index(request):
    message = "I defend calendars"
    return aiohttp.web.Response(text=message)

app = aiohttp.web.Application()
app.add_routes([aiohttp.web.get('/', index)])
app.add_routes([aiohttp.web.post('/push_event', receive_pushed_event)])
app.add_routes([aiohttp.web.get('/get_auth_link', get_auth_link)])
app.add_routes([aiohttp.web.post('/swap_auth_code', swap_auth_code)])
app.add_routes([aiohttp.web.post('/watch_calendar', watch_calendar)])

aiohttp.web.run_app(app)