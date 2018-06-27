# -*- coding: utf-8 -*-
import os
import json
from urllib.parse import urljoin
from logging import getLogger

from flask import current_app

import requests

from src import const

logger = getLogger(__name__)


class DestinationError(Exception):
    pass


class DestinationDoesNotExist(DestinationError):
    pass


class Destination:
    DESTINATION_LIST_URL = None

    @classmethod
    def get_destination_list_url(cls):
        if cls.DESTINATION_LIST_URL is None:
            if const.DESTINATION_ENDPOINT in os.environ:
                cls.DESTINATION_LIST_URL = urljoin(os.environ[const.DESTINATION_ENDPOINT], const.DESTINATION_LIST_PATH)
            else:
                cls.DESTINATION_LIST_URL = urljoin(current_app.config[const.DEFAULT_DESTINATION_ENDPOINT],
                                                   const.DESTINATION_LIST_PATH)
        return cls.DESTINATION_LIST_URL

    def get_destinations(self, name):
        headers = {
            'Content-Type': 'application/json'
        }
        params = {
            'filter': f'{const.DEST_NAME}|{name}'
        }
        try:
            destinations = requests.get(Destination.get_destination_list_url(), headers=headers, params=params).json()
            if len(destinations) == 0:
                raise DestinationDoesNotExist(f'destination({name}) does not found')
            return destinations[0]
        except json.JSONDecodeError as e:
            raise DestinationError(str(e))
