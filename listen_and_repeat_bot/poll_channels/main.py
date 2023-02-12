import os
import sys
import getpass
import asyncio
import logging

import yaml
from aiohttp import web
from telethon.tl.patched import Message

from poll_public_channel import PollPublicChannel


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


routes = web.RouteTableDef()


def parse_posts(posts):
    data = []
    for post in posts:
        message_parts = [ line.strip() for line in post.split("\n") ]

        if len(message_parts) < 2:
            logger.warning("Message is ignored due to incorrect "
                           "format, %s", post[:20])
            continue

        question = message_parts[0].lower()
        answers = [
                    answer.strip().lower()
                    for answer in message_parts[1].split("/")]
        examples = [
                        example.strip()
                        for example in message_parts[2:]]

        data.append({
            "question": question,
            "answers": answers,
            "examples": examples
        })
    return data


@routes.get('/data')
async def index_page(request):
    data = {"channels": []}

    for channel_opts in config["channels"]:
        posts = [
            post.message
            for post in poll_controller.get_channel_posts(
                        channel_opts["channel_id"])
            if isinstance(post, Message)
        ]
        channel_data = {
            **channel_opts,
            "data": parse_posts(posts)
        }
        data["channels"].append(channel_data)

    return web.json_response(data)

@routes.get('/status')
async def status(request):
    data = {"alive": "true"}
    return web.json_response(data)


async def run_http_server(routes, host, port):
    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    while True:
        await asyncio.sleep(3)


async def poll_channel_forever(poll_controller, config):
    while True:
        channel_id = config["channel_id"]
        message_limit = config["message_limit"]
        polling_interval = config["polling_interval"]

        await poll_controller.poll_channel(channel_id, message_limit)
        await asyncio.sleep(polling_interval)


def parse_listen_address(listen_address):
    if listen_address is None:
        return None, None
    items = listen_address.split(":")
    if len(items) == 1:
        return items[0], None
    elif len(items) == 2:
        return items[0], items[1]
    else:
        raise ValueError


def parse_config_file(filename):
    try:
        with open(filename, "r") as file:
            return yaml.safe_load(file)
    except (yaml.YAMLError, OSError) as exc:
        if isinstance(exc, OSError):
            print("Cannot read configuration file, "
                  "check path and permissions")
        if isinstance(exc, yaml.YAMLError):
            print("Config file has incorrect format, "
                  "cannot parse config options")
        return None


def create_poll_channel_controller(session_filename, api_id, api_hash):
    poll_channel = PollPublicChannel()

    # perform authentication
    auth_response = poll_channel.authenticate(
                        session_filename=session_filename,
                        api_id=api_id,
                        api_hash=api_hash)

    if auth_response[0] == 0:
        # successful authentication
        return poll_channel
    else:
        # cannot authenticate using provided session file
        return None



if __name__ == '__main__':
    session_filename = "listen_and_repeat.session"
    api_id = os.environ.get("API_ID", None)
    api_hash = os.environ.get("API_HASH", None)

    listen_address = os.environ.get("LISTEN_ADDRESS", None)
    host, port = parse_listen_address(listen_address)

    config = parse_config_file(
             os.environ.get("CONFIG_FILE", "config.yml"))
    if config is None:
        print("No correct config found, exiting")
        sys.exit(1)

    poll_controller = create_poll_channel_controller(
        session_filename=session_filename,
        api_id=api_id,
        api_hash=api_hash
    )
    if poll_controller is None:
        print("Cannot create poll controller, exiting")
        sys.exit(1)

    loop = asyncio.get_event_loop()
    loop.create_task(run_http_server(routes, host, port))
    for channel_opts in config["channels"]:
        loop.create_task(
            poll_channel_forever(poll_controller, channel_opts))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
