import asyncio
import sys

from httpx import HTTPStatusError

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET, TOKENS_FILE

# This uses the default client identification by OpenXbox
# Feel free to use your own here
client_id = CLIENT_ID
client_secret = CLIENT_SECRET
tokens_file = TOKENS_FILE

"""
For doing authentication, see xbox/webapi/scripts/authenticate.py
"""


async def async_main():
    async with SignedSession() as session:
        auth_mgr = AuthenticationManager(session, client_id, client_secret, "")

        try:
            with open(tokens_file) as f:
                tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.parse_raw(tokens)
        except FileNotFoundError:
            print(f"File {tokens_file} isn`t found or it doesn`t contain tokens!")
            exit(-1)

        try:
            await auth_mgr.refresh_tokens()
        except HTTPStatusError:
            print("Could not refresh tokens")
            sys.exit(-1)

        with open(tokens_file, mode="w") as f:
            f.write(auth_mgr.oauth.json())
        print(f"Refreshed tokens in {tokens_file}!")

        xbl_client = XboxLiveClient(auth_mgr)

        # Some example API calls
        # Get friendslist
        friendslist = await xbl_client.people.get_friends_own()
        print("Your friends:")
        print(friendslist)
        print()

        # Get presence status (by list of XUID)
        presence = await xbl_client.presence.get_presence_batch(
            ["2533274794093122", "2533274807551369"]
        )
        print("Statuses of some random players by XUID:")
        print(presence)
        print()

        # Get messages
        messages = await xbl_client.message.get_inbox()
        print("Your messages:")
        print(messages)
        print()

        # Get profile by GT
        profile = await xbl_client.profile.get_profile_by_gamertag("SomeGamertag")
        print("Profile under SomeGamertag gamer tag:")
        print(profile)
        print()


asyncio.run(async_main())
