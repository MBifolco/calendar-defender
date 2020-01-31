from models.model import *
from modules.async_http_request import AsyncHttpRequest
import asyncio
import aiohttp
import datetime
import jwt
import google.cloud.logging
import logging
import os

async def get_token(user):
    #access_token_expiration = datetime.strptime(user.access_token_expiration, "%a %b %d %H:%M:%S %Y")
    #if user.access_token_expiration < datetime.datetime.now():
    #logging.info("refresh token" + str(user.access_token_expiration))
    return await get_fresh_token(user)
    #else:
     #   return user.access_token

async def get_fresh_token(user):
    url = "https://www.googleapis.com/oauth2/v4/token"
   
    async_http_request = AsyncHttpRequest(url, user)
    await async_http_request.add_param("client_id",os.environ.get('CLIENT_ID'))
    await async_http_request.add_param("client_secret",os.environ.get('CLIENT_SECRET'))
    await async_http_request.add_param("refresh_token",user.refresh_token)
    await async_http_request.add_param("grant_type","refresh_token")
    await async_http_request.add_header("Content-Type","application/x-www-form-urlencoded")
    response = await async_http_request.make_request("post", False)

    if response:
        #remove 20 seconds to be sure 
        add_time_to_expiration = response["expires_in"] - 20
        access_token_expiration = datetime.datetime.now() + datetime.timedelta(seconds=add_time_to_expiration) 
        user.access_token_expiration = access_token_expiration
        user.access_token = response["access_token"] 
        user.save()
        return response["access_token"]
    

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
                print(await resp.text())
                if resp.status == 200:
                    response =  await resp.json()
                    
                    id_info = jwt.decode(response["id_token"], verify=False)                         
                    print(id_info)                   
                    try:
                        user = User.get(User.public_id == id_info["sub"])
                    # if use doesn't already exist just create new one
                    except Exception as e:
                        print(str(e))
                        user= User()
                        pass
                    
                    # Update all their info
                    user.public_id = id_info["sub"] 
                    user.email = id_info["email"]
                    user.access_token = response["access_token"]
                    #user.expires_in  = response["expires_in"]
                    user.refresh_token  = response["refresh_token"]
                    #user.scope  = response["scope"]
                    #user.token_type  = response["token_type"]
                    #user.id_token  = response["id_token"]
                    user.save()

                    return user
                else:
                    logging.info(await resp.text())
    except Exception as e:
        logging.error(str(e), exc_info=True)





