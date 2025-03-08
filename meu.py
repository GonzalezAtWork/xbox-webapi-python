import os
import sys
import asyncio
import json
import time
import subprocess

from httpx import HTTPStatusError
from urllib.parse import parse_qs
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET, TOKENS_FILE

sys.path.insert(0, os.path.dirname(__file__))

client_id = CLIENT_ID
client_secret = CLIENT_SECRET

last_activity_time = time.time() 
INACTIVITY_TIMEOUT = 600

def application(environ, start_response):
    global last_activity_time
    last_activity_time = time.time()

    query_string = environ.get('QUERY_STRING', '')
    params = parse_qs(query_string)
    device = params.get('device', [''])[0]
    action = params.get('action', [''])[0]
    game = params.get('game', [''])[0]

    message = ""

    if action == "status":
        status = asyncio.run(async_main(device, "status", None))
        message = json.dumps(status, default=lambda o: o.__dict__)
    if action == "launch":
        launch_app = asyncio.run(async_main(device, "launch_app", game))
        message = json.dumps(launch_app, default=lambda o: o.__dict__)
    if action == "reboot":
        reboot = asyncio.run(async_main(device, "reboot", None))
        message = json.dumps(reboot, default=lambda o: o.__dict__)
    if action == "terminate":
        terminate = asyncio.run(async_main(device, "terminate_app", None))
        message = json.dumps(terminate, default=lambda o: o.__dict__)
    if action == "logout":        
        terminate1 = asyncio.run(async_main(device, "terminate_app", None))
        terminate2 = asyncio.run(async_main(device, "terminate_app", None))
        terminate3 = asyncio.run(async_main(device, "terminate_app", None))
        sign_out1 = asyncio.run(async_main(device, "sign_out", None))
        sign_out2 = asyncio.run(async_main(device, "sign_out", None))
        sign_out3 = asyncio.run(async_main(device, "sign_out", None))
        message = json.dumps(sign_out3, default=lambda o: o.__dict__)
    if action == "login":        
        sign_in = asyncio.run(async_main(device, "sign_in", None))
        go_home = asyncio.run(async_main(device, "go_home", None))
        message = json.dumps(go_home, default=lambda o: o.__dict__)
    if action == "games":       
        status = asyncio.run(async_main(device, "status", None))
        games = asyncio.run(async_main(device, "games", None) )
        retorno = {"id":status.id,"name":status.name, "power_state": status.power_state,"games":[]}
        ids = []
        for app in games.result:
            if app.is_game:
                ids.append(str(app.one_store_product_id))                
        posters = asyncio.run(async_main(device, "posters", ids))
        for game in posters.products:
            filtered_poster = [item for item in game.localized_properties[0].images if item.image_purpose == "BoxArt"]
            lGame = {            
                "product_id": game.product_id,
                "image": filtered_poster[0].uri,
                "short_title": game.localized_properties[0].short_title,
                "product_title": game.localized_properties[0].product_title
            }
            retorno["games"].append(lGame)
        message = json.dumps(retorno, indent=4)
            
    start_response('200 OK', [('Content-Type', 'application/json')])
    return [message.encode('utf-8')]

async def async_main(device, command, params):
    global client_id, client_secret
    async with SignedSession() as session:   
        tokens_file = device + "_tokens.json"
        print(tokens_file)     
        auth_mgr = AuthenticationManager(session, client_id, client_secret, "")
        try:
            with open(tokens_file) as f:
                tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
        except FileNotFoundError as e:
            print(
                f"File {tokens_file} isn`t found or it doesn`t contain tokens! err={e}"
            )
            print("Authorizing via OAUTH")
            url = auth_mgr.generate_authorization_url()
            print(f"Auth via URL: {url}")
            authorization_code = input("Enter authorization code> ")
            tokens = await auth_mgr.request_oauth_token(authorization_code)
            auth_mgr.oauth = tokens
        try:
            await auth_mgr.refresh_tokens()
        except HTTPStatusError as e:
            print(
                f"""
                Could not refresh tokens from {tokens_file}, err={e}\n
                You might have to delete the tokens file and re-authenticate 
                if refresh token is expired
            """
            )
            sys.exit(-1)
        with open(tokens_file, mode="w") as f:
            f.write(auth_mgr.oauth.json())

        xbl_client = XboxLiveClient(auth_mgr)
        
        if command == "games":
            status = await xbl_client.smartglass.get_installed_apps(device)
        if command == "posters":
            status = await xbl_client.catalog.get_products(params)
        if command == "status":
            status = await xbl_client.smartglass.get_console_status(device)
        if command == "reboot":
            status = await xbl_client.smartglass.reboot(device)
        if command == "terminate_app":
            status = await xbl_client.smartglass.terminate_app(device)
        if command == "sign_out":
            status = await xbl_client.smartglass.sign_out(device)
        if command == "sign_in":
            status = await xbl_client.smartglass.sign_in(device)
        if command == "go_home":
            status = await xbl_client.smartglass.go_home(device)
        if command == "launch_app":
            status = await xbl_client.smartglass.launch_app(device, params)

        return status

async def reset_if_inactive():
    global last_activity_time
    while True:
        await asyncio.sleep(60)  # Check every minute
        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
            print("No connections for 10 minutes. Restarting script...")
            os.execv(sys.executable, [sys.executable] + sys.argv)  # Restart script

async def update_last_activity():
    global last_activity_time
    last_activity_time = time.time()

asyncio.run(reset_if_inactive())