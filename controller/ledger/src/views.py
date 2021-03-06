# -*- coding: utf-8 -*-
import os
import datetime
from logging import getLogger

import pytz

from flask import request, jsonify, current_app
from flask.views import MethodView
from werkzeug.exceptions import BadRequest

from pymongo import MongoClient
from bson.objectid import ObjectId

import cognitive_face as CF

from src import const, utils

from controllerlibs import DEST_NAME, DEST_FLOOR
from controllerlibs.services.orion import Orion, get_id, get_attr_value, NGSIPayloadError, AttrDoesNotExist
from controllerlibs.services.destination import Destination, DestinationDoesNotExist, DestinationFormatError
from controllerlibs.services.mixins import RobotFloorMapMixin
from controllerlibs.utils.start_movement import notify_start_movement

if const.FACE_API_KEY in os.environ:
    CF.Key.set(os.environ[const.FACE_API_KEY])
if const.FACE_API_BASEURL in os.environ:
    CF.BaseUrl.set(os.environ[const.FACE_API_BASEURL])

logger = getLogger(__name__)


class MongoMixin:
    def __init__(self):
        super().__init__()
        url = os.environ.get(const.MONGODB_URL, 'mongodb://localhost:27017')
        rs = os.environ.get(const.MONGODB_REPLICASET, None)

        if rs:
            client = MongoClient(url, replicaset=rs)
        else:
            client = MongoClient(url)
        self._collection = client[const.MONGODB_DATABASE][const.MONGODB_COLLECTION]


class RecordReceptionAPI(RobotFloorMapMixin, MongoMixin, MethodView):
    NAME = 'record-reception'

    def __init__(self):
        super().__init__()
        pepper_service = os.environ.get(const.PEPPER_SERVICE, '')
        pepper_service_path = os.environ.get(const.PEPPER_SERVICEPATH, '')
        self.pepper_type = os.environ.get(const.PEPPER_TYPE, '')

        self.pepper_orion = Orion(pepper_service, pepper_service_path)
        self.pepper_1_id = os.environ.get(const.PEPPER_1_ID, '')

        robot_service = os.environ.get(const.ROBOT_SERVICE, '')
        robot_service_path = os.environ.get(const.ROBOT_SERVICEPATH, '')
        self.robot_type = os.environ.get(const.ROBOT_TYPE, '')

        self.robot_orion = Orion(robot_service, robot_service_path)

    def post(self):
        content = request.data.decode('utf-8')
        logger.info(f'request content={content}')

        result = {'result': 'failure'}
        try:
            face = get_attr_value(content, 'face')
            dest = get_attr_value(content, 'dest')
            timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

            if face and os.path.isfile(face):
                face_ids = [r['faceId'] for r in CF.face.detect(face)]
            else:
                face_ids = []
                face = None

            data = {
                'status': 'reception',
                'face': face,
                'faceIds': face_ids,
                'dest': Destination().get_destination_by_name(dest),
                'receptionDatetime': timestamp,
            }
            logger.info(f'record reception, data={data}')
            oid = self._collection.insert_one(data).inserted_id

            dest_name = data['dest'].get(DEST_NAME)
            try:
                dest_floor = int(data['dest'].get(DEST_FLOOR))
            except (TypeError, ValueError):
                raise DestinationFormatError('dest_floor is invalid')

            handover_value = dest_floor
            if dest_floor == 1:
                robot_id = self.get_available_robot_from_floor(dest_floor)
                current_state = self.robot_orion.get_attrs(robot_id, 'r_state')['r_state']['value'].strip()

                if current_state == const.WAITING:
                    logger.info(f'call start-movement to guide_robot, dest_name={dest_name}, floor={dest_floor}')
                    notify_start_movement(os.environ.get(const.START_MOVEMENT_SERVICE, ''),
                                          os.environ.get(const.START_MOVEMENT_SERVICEPATH, ''),
                                          os.environ.get(const.START_MOVEMENT_ID, ''),
                                          os.environ.get(const.START_MOVEMENT_TYPE, ''),
                                          data['dest'], str(oid))
                else:
                    handover_value = 'busy'
                    message = f'cannot accept command at RecordReceptionAPI, current_state={current_state}, robot_id={robot_id}'
                    logger.warning(message)

                    timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                    update_data = {
                        'status': 'busy',
                        'busyDatetime': timestamp,
                    }
                    self._collection.update_one({"_id": oid}, {"$set": update_data})
            else:
                logger.info(f'nothing to do, dest_name={dest_name}, floor={dest_floor}')

            message = self.pepper_orion.send_cmd(self.pepper_1_id, self.pepper_type, 'handover', handover_value)
            result['result'] = 'success'
            result['message'] = message
        except AttrDoesNotExist as e:
            logger.error(f'AttrDoesNotExist: {str(e)}')
            raise BadRequest(str(e))
        except NGSIPayloadError as e:
            logger.error(f'NGSIPayloadError: {str(e)}')
            raise BadRequest(str(e))
        except DestinationFormatError as e:
            logger.error(f'DestinationFormatError: {str(e)}')
            raise BadRequest(str(e))
        except Exception as e:
            logger.exception(e)
            raise e

        return jsonify(result)


class RecordArrivalAPI(RobotFloorMapMixin, MongoMixin, MethodView):
    NAME = 'record-arrival'

    def __init__(self):
        super().__init__()
        robot_service = os.environ.get(const.ROBOT_SERVICE, '')
        robot_service_path = os.environ.get(const.ROBOT_SERVICEPATH, '')
        self.robot_type = os.environ.get(const.ROBOT_TYPE, '')

        self.robot_orion = Orion(robot_service, robot_service_path)

    def post(self):
        content = request.data.decode('utf-8')
        logger.info(f'request content={content}')

        result = {'result': 'failure'}
        try:
            id = get_id(content)
            arrival = get_attr_value(content, 'arrival')
            if arrival is not None:
                destination = Destination().get_destination_by_dest_human_sensor_id(id)
                if destination is not None and const.DEST_FLOOR in destination:
                    try:
                        floor = int(destination[const.DEST_FLOOR])
                    except (TypeError, ValueError):
                        raise DestinationFormatError('dest_floor is invalid')

                    robot_id = self.get_available_robot_from_floor(floor)
                    visitor_id = self.robot_orion.get_attrs(robot_id, 'visitor')['visitor']['value'].strip()

                    if visitor_id:
                        timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                        update_data = {
                            'status': 'arrival',
                            'arrivalDatetime': timestamp,
                        }
                        self._collection.update_one({"_id": ObjectId(visitor_id)}, {"$set": update_data})

                        attributes = [
                            {
                                'name': 'visitor',
                                'value': '',
                            }
                        ]
                        message = self.robot_orion.update_attributes(robot_id, self.robot_type, attributes)
                        result['result'] = 'success'
                        result['message'] = message
            logger.info(f'record arrival, id={id}, arrival={arrival}')
        except AttrDoesNotExist as e:
            logger.error(f'AttrDoesNotExist: {str(e)}')
            raise BadRequest(str(e))
        except NGSIPayloadError as e:
            logger.error(f'NGSIPayloadError: {str(e)}')
            raise BadRequest(str(e))
        except Exception as e:
            logger.exception(e)
            raise e

        return jsonify(result)


class DetectVisitorAPI(RobotFloorMapMixin, MongoMixin, MethodView):
    NAME = 'detect-visitor'

    def __init__(self):
        super().__init__()
        pepper_service = os.environ.get(const.PEPPER_SERVICE, '')
        pepper_service_path = os.environ.get(const.PEPPER_SERVICEPATH, '')
        self.pepper_type = os.environ.get(const.PEPPER_TYPE, '')

        self.pepper_orion = Orion(pepper_service, pepper_service_path)
        self.pepper_2_id = os.environ.get(const.PEPPER_2_ID, '')

        robot_service = os.environ.get(const.ROBOT_SERVICE, '')
        robot_service_path = os.environ.get(const.ROBOT_SERVICEPATH, '')
        self.robot_type = os.environ.get(const.ROBOT_TYPE, '')

        self.robot_orion = Orion(robot_service, robot_service_path)

        if const.FACE_VERIFY_DELTA_MIN in os.environ:
            try:
                self.face_verify_delta_min = int(os.environ[const.FACE_VERIFY_DELTA_MIN])
            except (TypeError, ValueError):
                self.face_verify_delta_min = current_app.config[const.DEFAULT_FACE_VERIFY_DELTA_MIN]
        else:
            self.face_verify_delta_min = current_app.config[const.DEFAULT_FACE_VERIFY_DELTA_MIN]

    def post(self):
        content = request.data.decode('utf-8')
        logger.info(f'request content={content}')

        result = {'result': 'failure'}
        try:
            face = get_attr_value(content, 'face')

            if face and os.path.isfile(face):
                face_ids = [result['faceId'] for result in CF.face.detect(face)]
            else:
                return jsonify(self.__send_reask())

            now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
            visitors = [utils.bson2dict(d) for d in self._collection.find({
                'status': 'reception',
                'dest.floor': 2,
                'receptionDatetime': {'$gte': now - datetime.timedelta(minutes=self.face_verify_delta_min)},
            }).sort([('receptionDatetime', -1), ])]

            def verify(visitors):
                for visitor in visitors:
                    for visitor_fid in visitor['faceIds']:
                        for fid in face_ids:
                            res = CF.face.verify(visitor_fid, fid)
                            res['visitor'] = visitor
                            yield res
                            if res['isIdentical']:
                                raise StopIteration
            verified = list(verify(visitors))
            if len(verified) == 0 or not verified[-1]['isIdentical']:
                return jsonify(self.__send_reask())
            else:
                logger.info(f'face api verify: identical result, {verified[-1]}')
                data = verified[-1]['visitor']

            dest_name = data['dest'].get(DEST_NAME)
            if not dest_name:
                raise DestinationFormatError('dest_name is empty')
            try:
                dest_floor = int(data['dest'].get(DEST_FLOOR))
            except (TypeError, ValueError):
                raise DestinationFormatError('dest_floor is invalid')

            handover_value = 'continue'
            if dest_floor == 2:
                robot_id = self.get_available_robot_from_floor(dest_floor)
                current_state = self.robot_orion.get_attrs(robot_id, 'r_state')['r_state']['value'].strip()

                if current_state == const.WAITING:
                    logger.info(f'call start-movement to guide_robot, dest_name={dest_name}, floor={dest_floor}')
                    notify_start_movement(os.environ.get(const.START_MOVEMENT_SERVICE, ''),
                                          os.environ.get(const.START_MOVEMENT_SERVICEPATH, ''),
                                          os.environ.get(const.START_MOVEMENT_ID, ''),
                                          os.environ.get(const.START_MOVEMENT_TYPE, ''),
                                          data['dest'], data['id'])
                else:
                    handover_value = 'busy'
                    message = f'cannot accept command at RecordReceptionAPI, current_state={current_state}, robot_id={robot_id}'
                    logger.warning(message)

                    timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                    update_data = {
                        'status': 'busy',
                        'busyDatetime': timestamp,
                    }
                    self._collection.update_one({"_id": ObjectId(data['id'])}, {"$set": update_data})

                message = self.pepper_orion.send_cmd(self.pepper_2_id, self.pepper_type, 'handover', handover_value)
                result['result'] = 'success'
                result['message'] = message
            else:
                logger.warning(f'invalid floor, dest_name={dest_name}, floor={dest_floor}')

        except AttrDoesNotExist as e:
            logger.error(f'AttrDoesNotExist: {str(e)}')
            raise BadRequest(str(e))
        except NGSIPayloadError as e:
            logger.error(f'NGSIPayloadError: {str(e)}')
            raise BadRequest(str(e))
        except DestinationDoesNotExist as e:
            logger.error(f'DestinationDoesNotFound: {str(e)}')
            raise BadRequest(str(e))
        except DestinationFormatError as e:
            logger.error(f'DestinationFormatError: {str(e)}')
            raise BadRequest(str(e))
        except Exception as e:
            logger.exception(e)
            raise e

        return jsonify(result)

    def __send_reask(self):
        try:
            message = self.pepper_orion.send_cmd(self.pepper_2_id, self.pepper_type, 'reask', 'true')
            result = {
                'result': 'success',
                'message': message,
            }
        except AttrDoesNotExist as e:
            logger.error(f'AttrDoesNotExist: {str(e)}')
            raise BadRequest(str(e))
        except NGSIPayloadError as e:
            logger.error(f'NGSIPayloadError: {str(e)}')
            raise BadRequest(str(e))
        except Exception as e:
            logger.exception(e)
            raise e

        return result


class ReaskDestinationAPI(RobotFloorMapMixin, MongoMixin, MethodView):
    NAME = 'reask-destination'

    def __init__(self):
        super().__init__()
        pepper_service = os.environ.get(const.PEPPER_SERVICE, '')
        pepper_service_path = os.environ.get(const.PEPPER_SERVICEPATH, '')
        self.pepper_type = os.environ.get(const.PEPPER_TYPE, '')

        self.pepper_orion = Orion(pepper_service, pepper_service_path)
        self.pepper_2_id = os.environ.get(const.PEPPER_2_ID, '')

        robot_service = os.environ.get(const.ROBOT_SERVICE, '')
        robot_service_path = os.environ.get(const.ROBOT_SERVICEPATH, '')
        self.robot_type = os.environ.get(const.ROBOT_TYPE, '')

        self.robot_orion = Orion(robot_service, robot_service_path)

    def post(self):
        content = request.data.decode('utf-8')
        logger.info(f'request content={content}')

        result = {'result': 'failure'}
        try:
            dest = get_attr_value(content, 'dest')
            timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

            data = {
                'status': 'reask',
                'face': None,
                'faceIds': [],
                'dest': Destination().get_destination_by_name(dest),
                'reaskDatetime': timestamp,
            }
            logger.info(f'record reask, data={data}')
            oid = self._collection.insert_one(data).inserted_id

            dest_name = data['dest'].get(DEST_NAME)
            try:
                dest_floor = int(data['dest'].get(DEST_FLOOR))
            except (TypeError, ValueError):
                raise DestinationFormatError('dest_floor is invalid')

            handover_value = 'continue'
            if dest_floor == 2:
                robot_id = self.get_available_robot_from_floor(dest_floor)
                current_state = self.robot_orion.get_attrs(robot_id, 'r_state')['r_state']['value'].strip()

                if current_state == const.WAITING:
                    logger.info(f'call start-movement to guide_robot, dest_name={dest_name}, floor={dest_floor}')
                    notify_start_movement(os.environ.get(const.START_MOVEMENT_SERVICE, ''),
                                          os.environ.get(const.START_MOVEMENT_SERVICEPATH, ''),
                                          os.environ.get(const.START_MOVEMENT_ID, ''),
                                          os.environ.get(const.START_MOVEMENT_TYPE, ''),
                                          data['dest'], str(oid))
                else:
                    handover_value = 'busy'
                    message = f'cannot accept command at RecordReceptionAPI, current_state={current_state}, robot_id={robot_id}'
                    logger.warning(message)

                    timestamp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                    update_data = {
                        'status': 'busy',
                        'busyDatetime': timestamp,
                    }
                    self._collection.update_one({"_id": oid}, {"$set": update_data})

                message = self.pepper_orion.send_cmd(self.pepper_2_id, self.pepper_type, 'handover', handover_value)
                result['result'] = 'success'
                result['message'] = message
            else:
                logger.info(f'nothing to do, dest_name={dest_name}, floor={dest_floor}')

        except AttrDoesNotExist as e:
            logger.error(f'AttrDoesNotExist: {str(e)}')
            raise BadRequest(str(e))
        except NGSIPayloadError as e:
            logger.error(f'NGSIPayloadError: {str(e)}')
            raise BadRequest(str(e))
        except Exception as e:
            logger.exception(e)
            raise e

        return jsonify(result)
