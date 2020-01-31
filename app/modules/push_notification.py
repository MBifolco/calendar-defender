from modules.async_http_request import AsyncHttpRequest
import asyncio
import aiohttp
import google.cloud.logging
import logging
import os
import modules.token as token
from modules.event import Event

class PushNotification(object):

    def __init__(self, watched_calendar, user):
        self.watched_calendar = watched_calendar
        self.user = user

    async def get_updated_events(self):

        url = "https://www.googleapis.com/calendar/v3/calendars/" + self.watched_calendar.calendar_id + "/events/"

        pages = True
        self.updated_events = []
        i = 0
        try:
            while pages:
                async_http_request = AsyncHttpRequest(url, self.user)
                await async_http_request.add_param("orderBy","updated")
                await async_http_request.add_param("singleEvents","True")
                await async_http_request.add_param("showDeleted","False")
                await async_http_request.add_param("updatedMin",self.watched_calendar.last_check)
                try:
                    await async_http_request.add_param("pageToken",nextPageToken)
                except:
                    pass
                response = await async_http_request.make_request("get")
                #print(response)
                if response:
                    self.updated_events.extend(response["items"])
                    try:
                        nextPageToken = response["nextPageToken"]
                        print (nextPageToken)
                    except:
                        pages = False
                else:
                    pages = False    
               
                await self._update_wactched_calendar_last_check()

            return self.updated_events

        except Exception as e:
            logging.error(str(e), exc_info=True)

    async def _update_wactched_calendar_last_check(self):
        try:
            for updated_event in reversed(self.updated_events) :
                if "updated" in updated_event:
                    last_check = updated_event["updated"]
                    #print("last update " + str(last_check))
                    self.watched_calendar.last_check = last_check
                    #self.watched_calendar.save()
                    break
        except Exception as e:
            logging.error(str(e), exc_info=True)

        
    async def decline_if_busy(self, updated_event):
        event = Event(updated_event)   
        
        if await event.is_needs_action():
            busy = await event.is_busy_during_event(self.watched_calendar, self.user)
            logging.info("checked: " + str(updated_event["id"]) + ": " + str(busy))
            
            if busy: 
                reject = await event.decline_meeting(self.watched_calendar, self.user)
                logging.info(str(updated_event["id"]) + " was rejected")
            #else:
                #logging.info(str(updated_event["id"]) + " you're free")
        #else:
            #logging.info(str(updated_event["id"]) + " you've already responded")