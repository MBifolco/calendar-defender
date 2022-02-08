import asyncio
import aiohttp
import google.cloud.logging
import logging
import modules.token as token

class Calendar(object):
    
    async def get_calendars():
        calendar_id = "xxx"
        url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
        headers = {'Authorization' : "Bearer " + await token.get_token(user)}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    print(await resp.text())
                    if resp.status == 200:
                        response = await res.json()
                        calendar_id_list =[]
                        for calendar in response["items"]:
                            calendar_id_list = calendar_id_list.append(calendar["id"])
                        return calendar_id_list
                    else:
                        logging.info(await resp.text())
        except Exception as e:
            logging.info(str(e)) 
