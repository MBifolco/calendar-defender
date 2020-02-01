from modules.google_calendar_async_http_request import GoogleCalendarAsyncHttpRequest
import asyncio
import aiohttp
import base64
import google.cloud.logging
import logging
import os
import modules.token as token

class Event(object):
    def __init__(self, event):
        self.event = event

    async def get_self_from_attendees(self):
        for attendee in self.event["attendees"]:
            if "self" in attendee:
                return attendee


    async def get_self_response_status(self):
        if "attendees" in self.event:
            attendee = await self.get_self_from_attendees()
            if attendee["self"] == True:
                return attendee

    async def is_attending(self):
        attendee = await self.get_self_response_status()
        try:
            if attendee["responseStatus"] == "accepted":
                return True
            return False
        except:
            return False

    async def is_needs_action(self):
        attendee = await self.get_self_response_status()
        try:
            if attendee["responseStatus"] == "needsAction":
                return True
            return False
        except:
            return False

    async def is_organizer(self):
        try:
            if "self" in self.event["organizer"]:
                if self.event["organizer"]["self"] == True:
                    return True
        except:
            return False
        return False

    async def is_transparent(self):
        try:
            if self.event["transparency"] == "transparent":
                return True
        except:
            return False
        return False

    async def get_event_id(self):
        return self.event["id"]

    async def is_busy_during_event(self, calendar, user):
        url = "https://www.googleapis.com/calendar/v3/calendars/calendarId/events"
        google_calendar_async_http_request = GoogleCalendarAsyncHttpRequest(user)
        await google_calendar_async_http_request.add_param("calendarId", calendar.calendar_id)
        await google_calendar_async_http_request.add_param("timeMin", self.event["start"]["dateTime"])
        await google_calendar_async_http_request.add_param("timeMax", self.event["end"]["dateTime"] )
        
        #await async_http_request.add_header("Content-Type", "")
        response = await google_calendar_async_http_request.make_request("get", url)
        #print(response)
        if response:
            for item in response['items']:
                competing_event = Event(item)
                #print (competing_event.event)
                if (await competing_event.is_attending() or await competing_event.is_organizer()) and await competing_event.get_event_id() != self.event["id"] and not await competing_event.is_transparent():
                    return True
            return False
        else:
            return False

        

    async def decline_meeting(self, calendar, user):
        url = "https://www.googleapis.com/calendar/v3/calendars/" + calendar.calendar_id+ "/events/" + self.event["id"]
        attendee = await self.get_self_from_attendees()
        attendee["responseStatus"] = "declined"
        attendee["comment"] = "Declined automatically by Calendar Defense."

        google_calendar_async_http_request = GoogleCalendarAsyncHttpRequest(user)
        await google_calendar_async_http_request.add_param("sendUpdates", "all")
        await google_calendar_async_http_request.add_json("attendees", [attendee])
        response = await google_calendar_async_http_request.make_request("patch", url)
      
        if response:
            return True
        return False