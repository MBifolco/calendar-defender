from aiohttp import web
import asyncio
import aiohttp

async def get_fresh_token():
    url = "https://www.googleapis.com/oauth2/v4/token"
    token = "1//05iGZRo-z0rRuCgYIARAAGAUSNwF-L9IrGzBcHJcml97e3VvviDW2JYqraRAhWAS-XM3cfiOvayPhalyXV5hc-kdev-DqTLvm1Q4"
    params = {
        "client_id": "223090476821-41ioedrp1k906f6hgslic39u6sdrcas3.apps.googleusercontent.com", 
        "client_secret": "jGwWd7FVCwvgDxp8VZxCirYD", 
        "refresh_token": token, 
        "grant_type": "refresh_token"
    }
    headers = {
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params) as resp:
                response =  await resp.json()
                if resp.status == 200:
                    return response['access_token']
                else:
                    print(await resp.text())
    except:
        pass
  


async def get_event(resource_id, retry=False):
    calendar_id = "mdb388@gmail.com"
    url = "https://www.googleapis.com/calendar/v3/calendars/" + calendar_id+ "/events/" + resource_id
    token = await get_fresh_token()
    auth_string = "Bearer " + token
    headers = {'Authorization' : auth_string}
    
    try: 
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(await resp.text())
    except:
        pass

async def index(request):
    return web.Response(text="I defend calendars.")

async def receive_pushed_event(request):
    try:
        channel_id = request.headers["X-Goog-Channel-ID"]
        message_number  = request.headers["X-Goog-Message-Number"]
        resource_id = request.headers["X-Goog-Resource-ID"]
        resource_state  = request.headers["X-Goog-Resource-State"]
        resource_uri = request.headers["X-Goog-Resource-URI"]

        event = await get_event(resource_id)
        print(event)

        return web.Response(text="thanks for letting us know")

    except:
        return web.HTTPBadRequest()
    

app = web.Application()
app.add_routes([web.get('/', index)])
app.add_routes([web.get('/push_event', receive_pushed_event)])

web.run_app(app)