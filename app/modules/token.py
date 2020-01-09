from google.cloud import logging
import asyncio
import aiohttp
import datetime
import os

logging_client = logging.Client()
log_name = 'calendar-defender-debug'
logger = logging_client.logger(log_name)


async def get_token(user):
    #access_token_expiration = datetime.strptime(user.access_token_expiration, "%a %b %d %H:%M:%S %Y")
    if user.access_token_expiration < datetime.datetime.now():
        logger.log_text("refresh token" + str(user.access_token_expiration))
        return await get_fresh_token(user)
    else:
        return user.access_token

async def get_fresh_token(user):
    url = "https://www.googleapis.com/oauth2/v4/token"
    ##### replace with user token
    params = {
        "client_id": os.environ.get('CLIENT_ID'),
        "client_secret": os.environ.get('CLIENT_SECRET'),
        "refresh_token": user.refresh_token, 
        "grant_type": "refresh_token"
    }
    headers = {
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    response =  await resp.json()
                    #remove 20 seconds to be sure 
                    add_time_to_expiration = response["expires_in"] - 20
                    access_token_expiration = datetime.datetime.now() + datetime.timedelta(seconds=add_time_to_expiration) 
                    user.access_token_expiration = access_token_expiration
                    user.access_token = response["access_token"] 
                    user.save()
                    return response["access_token"]
                else:
                    logger.log_text(await resp.text())
    except Exception as e:
        logger.log_text(str(e))

async def trade_authcode_for_token(authcode):
    url = "https://www.googleapis.com/oauth2/v4/token"
    params = {
        "code": authcode,
        "client_id": os.environ.get('CLIENT_ID'),
        "client_secret": os.environ.get('CLIENT_SECRET'),
        "redirect_uri": "https://calendardefense.com",
        "grant_type": "authorization_code"
    }
    headers = {
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    response =  await resp.json()
                    user = User
                    user = User()
                    id_info = user.get_id_info(response["id_token"])
                    user.google_id = id_info["sub"] 
                    user.email = id_info["email"]
                    user.access_token = response["access_token"]
                    user.expires_in  = response["expires_in"]
                    user.refresh_token  = response[""]
                    user.scope  = response["scope"]
                    user.token_type  = response["token_type"]
                    user.id_token  = response["id_token"]
                    return response
                else:
                    logger.log_text(await resp.text())
    except Exception as e:
        logger.log_text(str(e))





