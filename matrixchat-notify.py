#!/usr/bin/env python3
"""Notify of drone.io CI pipeline results on Matrix chat.

Requires:

* <https://github.com/poljar/matrix-nio>
* Optional: <https://pypi.org/project/markdown/>

"""

import argparse
import asyncio
import json
import logging
import os
import sys
from distutils.util import strtobool
from os.path import exists
from string import Template

from nio import AsyncClient, LoginResponse

PROG = "matrixchat-notify"
CONFIG_FILENAME = f"{PROG}-config.json"
DEFAULT_TEMPLATE = "${DRONE_BUILD_STATUS}"
DEFAULT_HOMESERVER = "https://matrix.org"
SETTINGS_KEYS = (
    "accesstoken",
    "deviceid",
    "devicename",
    "homeserver",
    "markdown",
    "password",
    "roomid",
    "template",
    "userid",
)
log = logging.getLogger(PROG)


def tobool(s):
    try:
        return strtobool(s)
    except ValueError:
        return False


def read_config_from_file_and_env(filename):
    config = {}

    if exists(filename):
        with open(filename) as fp:
            config = json.load(fp)

    for setting in SETTINGS_KEYS:
        val = os.getenv("PLUGIN_" + setting.upper())

        if val is not None:
            config[setting] = val

        if not config.get(setting):
            log.debug(f"Configuration setting '{setting}' not set or empty in config.")

    return config


async def send_notification(config, message):
    token = config.get("accesstoken")
    device_id = config.get("deviceid")
    homeserver = config.get("homeserver", DEFAULT_HOMESERVER)

    client = AsyncClient(homeserver, config["userid"])
    log.debug("Created AsyncClient: %r", client)

    if token and device_id:
        log.debug("Using access token for authentication.")
        client.access_token = token
        client.device_id = device_id
    else:
        log.debug("Trying to log in with password...")
        resp = await client.login(config["password"], device_name=config.get("devicename"))

        # check that we logged in succesfully
        if isinstance(resp, LoginResponse):
            log.debug("Matrix login successful.")
            log.debug("Access token: %s", resp.access_token)
            log.debug("Device ID: %s", resp.device_id)
        else:
            log.error(f"Failed to log in: {resp}")
            await client.close()
            return

    if isinstance(message, dict):
        message.setdefault("msgtype", "m.notice")
        resp = await client.room_send(
            config["roomid"], message_type="m.room.message", content=message
        )
    else:
        resp = await client.room_send(
            config["roomid"],
            message_type="m.room.message",
            content={"msgtype": "m.notice", "body": message},
        )

    log.info(
        "Sent notification message to %s. Response status: %s",
        homeserver,
        resp.transport_response.status,
    )
    await client.close()


def main(args=None):
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.splitlines()[0])
    ap.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        default=CONFIG_FILENAME,
        help="Configuration file path (default: '%(default)s')",
    )
    ap.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Don't send notification message, only print it.",
    )
    ap.add_argument(
        "-m",
        "--render-markdown",
        action="store_true",
        help="Message is in Markdown format and will be rendered to HTML.",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug level logging.",
    )

    args = ap.parse_args(args)

    logging.basicConfig(
        level="DEBUG" if args.verbose else os.environ.get("PLUGIN_LOG_LEVEL", "INFO").upper(),
        format=os.environ.get("PLUGIN_LOG_FORMAT", "%(levelname)s: %(message)s"),
    )

    try:
        config = read_config_from_file_and_env(args.config)
    except Exception as exc:
        return f"Could not parse configuration: {exc}"

    template = config.get("template", DEFAULT_TEMPLATE)
    message = Template(template).safe_substitute(os.environ)

    if tobool(config.get("markdown")) or args.render_markdown:
        log.debug("Rendering markdown message to HTML.")
        try:
            import markdown

            formatted = markdown.markdown(message)
        except:  ## noqa
            log.exception("Failed to render message with markdown.")
            return 1

        body = message
        message = {"formatted_body": formatted}
        message["body"] = body
        message["format"] = "org.matrix.custom.html"

    if not args.dry_run:
        if not config.get("userid"):
            return "userid not found in configuration."

        if not config.get("roomid"):
            return "roomid not found in configuration."

        if not config.get("password") and not config.get("accesstoken"):
            return "No password or accesstoken found in configuration."

        try:
            log.debug("Sending notification to Matrix chat...")
            asyncio.run(send_notification(config, message))
        except KeyboardInterrupt:
            log.info("Interrupted.")
    else:
        print(message)


if __name__ == "__main__":
    sys.exit(main() or 0)
