# -*- coding: utf-8 -*-
import os

# logging
LOGGING_JSON = os.environ.get('LOGGING_JSON', '../docker/logging.json')
TARGET_HANDLERS = ['console', ]

# flask config
CONFIG_CFG = 'config.cfg'
DEFAULT_PORT = 'DEFAULT_PORT'
DEFAULT_ORION_ENDPOINT = 'DEFAULT_ORION_ENDPOINT'
DEFAULT_DESTINATION_ENDPOINT = 'DEFAULT_DESTINATION_ENDPOINT'

# environment variable name
LOG_LEVEL = 'LOG_LEVEL'
LISTEN_PORT = 'LISTEN_PORT'
ORION_ENDPOINT = 'ORION_ENDPOINT'
DESTINATION_ENDPOINT = 'DESTINATION_ENDPOINT'
ROBOT_FLOOR_MAP = 'ROBOT_FLOOR_MAP'

# orion specification
ORION_GET_PATH = '/v2/entities/'
ORION_POST_PATH = '/v1/updateContext'
ORION_PAYLOAD_TEMPLATE = {
    'contextElements': [
        {
            'id': '',
            'isPattern': False,
            'type': '',
            'attributes': [],
        },
    ],
    'updateAction': 'UPDATE',
}

# destination specification
DESTINATION_LIST_PATH = '/'
DEST_NAME = 'name'
DEST_POS_X = 'dest_pos_x'
DEST_POS_Y = 'dest_pos_y'
DEST_FLOOR = 'floor'
