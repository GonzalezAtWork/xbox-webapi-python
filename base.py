import asyncio
import sys

from httpx import HTTPStatusError

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET, TOKENS_FILE

"""
This uses the global default client identification by OpenXbox
You can supply your own parameters here if you are permitted to create
new Microsoft OAuth Apps and know what you are doing
"""
client_id = CLIENT_ID
client_secret = CLIENT_SECRET

"""
For doing authentication, see xbox/webapi/scripts/authenticate.py
"""


async def async_main():
    # Create a HTTP client session
    async with SignedSession() as session:
        
        tokens_file = "F4001C3736C95FF5_tokens.json"
        """
        Initialize with global OAUTH parameters from above
        """
        auth_mgr = AuthenticationManager(session, client_id, client_secret, "")

        """
        Read in tokens that you received from the `xbox-authenticate`-script previously
        See `xbox/webapi/scripts/authenticate.py`
        """
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

        """
        Refresh tokens, just in case
        You could also manually check the token lifetimes and just refresh them
        if they are close to expiry
        """
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

        # Save the refreshed/updated tokens
        with open(tokens_file, mode="w") as f:
            f.write(auth_mgr.oauth.json())
        print(f"Refreshed tokens in {tokens_file}!")

        """
        Construct the Xbox API client from AuthenticationManager instance
        """
        xbl_client = XboxLiveClient(auth_mgr)

        """
        Some example API calls
        # Get friendslist
        friendslist = await xbl_client.people.get_friends_own()
        print(f"Your friends: {friendslist}\n")

        # Get presence status (by list of XUID)
        presence = await xbl_client.presence.get_presence_batch(
            ["2533274794093122", "2533274807551369"]
        )
        print(f"Statuses of some random players by XUID: {presence}\n")

        # Get messages
        messages = await xbl_client.message.get_inbox()
        print(f"Your messages: {messages}\n")

        # Get profile by GT
        profile = await xbl_client.profile.get_profile_by_gamertag("SomeGamertag")
        print(f"Profile under SomeGamertag gamer tag: {profile}\n")
get_profile_by_xuid
        """
        
        status = await xbl_client.smartglass.get_console_status("F4001C3736C95FF5")
        print(f"Status response: {status}\n")
                
        """
        
        profile = await xbl_client.profile.get_profile_by_gamertag("D10 0007")
        print(f"Profile under SomeGamertag gamer tag: {profile}\n")

        press_button_new = await xbl_client.smartglass.press_button_new("F4001EB523DF1ADD","Nexus")
        print(f"Reboot response: {press_button_new}\n")
        
        terminate_app = await xbl_client.smartglass.terminate_app("F4001EB523DF1ADD")
        print(f"terminate_app response: {terminate_app}\n")
                
        launch_app = await xbl_client.smartglass.launch_app("F4001EB523DF1ADD","9NZQPT0MWTD0")
        print(f"launch_app response: {launch_app}\n")
        
        consoles = await xbl_client.smartglass.get_console_list()
        print(f"Console List: {consoles}\n")
        
        status = await xbl_client.smartglass.get_console_status(consoles.result[0].id)
        print(f"Status response: {status}\n")
        
        apps = await xbl_client.smartglass.get_installed_apps(consoles.result[0].id)
        print(f"Apps response: {apps}\n")
        
        go_home = await xbl_client.smartglass.go_home(consoles.result[0].id)
        print(f"go_home response: {go_home}\n")
        
        reboot = await xbl_client.smartglass.reboot(consoles.result[0].id)
        print(f"Reboot response: {reboot}\n")
        """
    
    
asyncio.run(async_main())
