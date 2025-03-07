# http://localhost:8666/status?device=F4001C3736C95FF5 = D10-S0033 = d10-0007@decaedro.net - LiveTim
# http://localhost:8666/status?device=F4001C380A9DE799 = D10-S0088 = d10-0042@decaedro.net - Vivo
# http://localhost:8666/status?device=F4001C19F3D99ED0 = D10-S0011 = zel_santo@hotmail.com - NET

import flask
import sys
import asyncio
import sys
import json

from flask import g, Response
from httpx import HTTPStatusError
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET, TOKENS_FILE

client_id = CLIENT_ID
client_secret = CLIENT_SECRET
#tokens_file = TOKENS_FILE.replace("tokens",device + "_tokens")
tokens_file = ""

xbl_client = None

async def async_main(device, command, params):
    tokens_file = device + "_tokens.json"
    global xbl_client
    async with SignedSession() as session:
        auth_mgr = AuthenticationManager(session, client_id, client_secret, "")
        try:
            with open(tokens_file) as f:
                tokens = f.read()
            # Assign gathered tokens
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
        print(f"Refreshed tokens in {tokens_file.replace('tokens',device + '_tokens')}!")
        xbl_client = XboxLiveClient(auth_mgr)	
        if command == "games":
            return await xbl_client.smartglass.get_installed_apps(device)
        if command == "posters":
            return await xbl_client.catalog.get_products(params)
        if command == "status":
            return await xbl_client.smartglass.get_console_status(device)
        if command == "reboot":
            return await xbl_client.smartglass.reboot(device)
        if command == "terminate_app":
            return await xbl_client.smartglass.terminate_app(device)
        if command == "sign_out":
            return await xbl_client.smartglass.sign_out(device)
        if command == "sign_in":
            return await xbl_client.smartglass.sign_in(device)
        if command == "go_home":
            return await xbl_client.smartglass.go_home(device)
        if command == "launch_app":
            return await xbl_client.smartglass.launch_app(device, params)
			
			
			
		
PORT = 8666 if '--port' not in sys.argv else int(sys.argv[sys.argv.index('--port') + 1])
APP = flask.Flask(__name__)
		
		
@APP.route("/status", methods=["GET"])
async def status():
	device = flask.request.args.get("device")
	
	status = await async_main(device, "status", None)
	
	return Response( json.dumps(status, default=lambda o: o.__dict__) , mimetype="application/json")
	
		
@APP.route("/launch", methods=["GET"])
async def launch():
	device = flask.request.args.get("device")
	game = flask.request.args.get("game")
	
	launch_app = await async_main(device, "launch_app", game)
	
	return Response( json.dumps(launch_app, default=lambda o: o.__dict__) , mimetype="application/json")
	
@APP.route("/reboot", methods=["GET"])
async def reboot():
	device = flask.request.args.get("device")
	
	reboot = await async_main(device, "reboot", None)
	
	return Response( json.dumps(reboot, default=lambda o: o.__dict__) , mimetype="application/json")

@APP.route("/terminate", methods=["GET"])
async def terminate():
	device = flask.request.args.get("device")
	
	terminate = await async_main(device, "terminate_app", None)
	
	return Response( json.dumps(terminate, default=lambda o: o.__dict__) , mimetype="application/json")
	
@APP.route("/logout", methods=["GET"])
async def logout():
	device = flask.request.args.get("device")
	
	terminate1 = await async_main(device, "terminate_app", None)
	terminate2 = await async_main(device, "terminate_app", None)
	terminate3 = await async_main(device, "terminate_app", None)
	sign_out1 = await async_main(device, "sign_out", None)
	sign_out2 = await async_main(device, "sign_out", None)
	sign_out3 = await async_main(device, "sign_out", None)
	
	return Response( json.dumps(sign_out3, default=lambda o: o.__dict__) , mimetype="application/json")
	
	
@APP.route("/login", methods=["GET"])
async def login():
	device = flask.request.args.get("device")
	
	sign_in = await async_main(device, "sign_in", None)
	go_home = await async_main(device, "go_home", None)
	
	return Response( json.dumps(go_home, default=lambda o: o.__dict__) , mimetype="application/json")
	
	
@APP.route("/games", methods=["GET"])
async def games():
	device = flask.request.args.get("device")
	print("device: ", device)
	status = await async_main(device, "status", None)
	games = await async_main(device, "games", None)
	retorno = {"id":status.id,"name":status.name, "power_state": status.power_state,"games":[]}
	ids = []
	for app in games.result:
		if app.is_game:
			ids.append(str(app.one_store_product_id))
			
	posters = await async_main(device, "posters", ids)

	for game in posters.products:
		filtered_poster = [item for item in game.localized_properties[0].images if item.image_purpose == "BoxArt"]
		lGame = {
		
			"product_id": game.product_id,
			"image": filtered_poster[0].uri,
			"short_title": game.localized_properties[0].short_title,
			"product_title": game.localized_properties[0].product_title
		}
		retorno["games"].append(lGame)
		
	return Response( json.dumps(retorno, indent=4) , mimetype="application/json")

def startManager():
	APP.run(host='0.0.0.0', port=PORT, threaded=False)
				
if __name__ == "__main__":
	startManager()
	

