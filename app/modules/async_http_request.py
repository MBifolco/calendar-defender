import asyncio
import aiohttp
import google.cloud.logging
import modules.token as token
import logging
import os

class AsyncHttpRequest(object):

    def __init__(self):
        self.headers = dict()
        self.params = dict()
        self.json = dict()

    async def add_param(self, key, value):
        self.params[key] = value

    async def add_header(self, key, value):
        self.headers[key] = value

    async def add_json(self, key, value):
        self.json[key] = value

    async def make_request(self, method, url):
        if not self.headers:
            self.headers = None
        if not self.params:
            self.params = None
        if not self.json:
            self.json = None
        
        
        try:
            async with aiohttp.ClientSession() as session:
                methods = {
                    "get" : session.get,
                    "post" : session.post,
                    "patch" : session.patch
                }
                print(self.params)
                async with methods[method](url, headers=self.headers, params=self.params, json=self.json) as resp:
                    #print(await resp.text())
                    if resp.status == 200:
                        #print(await resp.json())
                        return await resp.json()
                    else:
                        logging.info(await resp.text())
                        return False
        except Exception as e:
            logging.error(str(e), exc_info=True)
    