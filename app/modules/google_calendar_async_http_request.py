from modules.async_http_request import AsyncHttpRequest
import asyncio
import aiohttp
import datetime
import google.cloud.logging
import logging
import os

class GoogleCalendarAsyncHttpRequest(AsyncHttpRequest):

    def __init__(self, user):
        self.user = user
        super().__init__()

    async def get_token(self):
        
        logging.info(self.user.access_token_expiration)
        logging.info(datetime.datetime.now())
        if self.user.access_token_expiration < datetime.datetime.now():
            logging.info("refresh token" + str(self.user.access_token_expiration))
            return await self.get_fresh_token()
        else:
            return self.user.access_token

    async def get_fresh_token(self):
        url = "https://www.googleapis.com/oauth2/v4/token"
       
        async_http_request = AsyncHttpRequest()
        await async_http_request.add_param("client_id",os.environ.get('CLIENT_ID'))
        await async_http_request.add_param("client_secret",os.environ.get('CLIENT_SECRET'))
        await async_http_request.add_param("refresh_token",self.user.refresh_token)
        await async_http_request.add_param("grant_type","refresh_token")
        await async_http_request.add_header("Content-Type","application/x-www-form-urlencoded")
        response = await async_http_request.make_request("post", url)

        if response:
            #remove 20 seconds to be sure 
            add_time_to_expiration = response["expires_in"] - 20
            access_token_expiration = datetime.datetime.now() + datetime.timedelta(seconds=add_time_to_expiration) 
            self.user.access_token_expiration = access_token_expiration
            self.user.access_token = response["access_token"] 
            self.user.save()
            return response["access_token"]

    async def make_request(self, method, url, auth=True):
        if auth:
            self.headers['Authorization'] = "Bearer " + await self.get_token()

        return await super().make_request(method, url)

    