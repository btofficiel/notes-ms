# Importing modules

import tornado.web
import logging
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Tuple,
    Dict,
    Optional,
    Type
)
import traceback
import json
import uuid
from notesservice.service import NotesService
from notesservice import LOGGER_NAME
import notesservice.utils.logutils as logutils

NOTES_LIST_REGEX = r'/notes/?'
NOTES_REGEX = r'/notes/(?P<id>[a-zA-Z0-9-]+)/?'
APP_VERSION = r'/v1'
NOTES_ENTRY_URI_FORMAT_SR = r'/notes/{id}'


# Creating BaseRequestHandler class
class BaseRequestHandler(tornado.web.RequestHandler):
    def initialize(
        self,
        service: NotesService,
        config: Dict,
        logger: logging.Logger
    ) -> None:
        self.service = service
        self.config = config
        self.logger = logger

    def prepare(self) -> Optional[Awaitable[None]]:
        req_id = uuid.uuid4().hex
        logutils.set_log_context(
            req_id=req_id,
            method=self.request.method,
            uri=self.request.uri,
            ip=self.request.remote_ip
        )

        logutils.log(
            self.logger,
            logging.DEBUG,
            include_context=True,
            message='REQUEST'
        )

        return super().prepare()

    def on_finish(self) -> None:
        super().on_finish()

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        body = {
            'method': self.request.method,
            'uri': self.request.path,
            'code': status_code,
            'message': self._reason
        }

        logutils.set_log_context(reason=self._reason)

        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            logutils.set_log_context(exc_info=exc_info)
            if self.settings.get('serve_traceback'):
                # in debug mode, send a traceback
                trace = '\n'.join(traceback.format_exception(*exc_info))
                body['trace'] = trace

        self.finish(body)

    def log_exception(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        # https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.log_exception
        if isinstance(value, tornado.web.HTTPError):
            if value.log_message:
                msg = value.log_message % value.args
                logutils.log(
                    tornado.log.gen_log,
                    logging.WARNING,
                    status=value.status_code,
                    request_summary=self._request_summary(),
                    message=msg
                )
        else:
            logutils.log(
                tornado.log.app_log,
                logging.ERROR,
                message='Uncaught exception',
                request_summary=self._request_summary(),
                request=repr(self.request),
                exc_info=(typ, value, tb)
            )


# Creating DefaultRequestHandler class
class DefaultRequestHandler(BaseRequestHandler):
    def initialize(  # type: ignore
        self,
        status_code: int,
        message: str,
        logger: logging.Logger
    ):
        self.logger = logger
        self.set_status(status_code, reason=message)

    def prepare(self) -> Optional[Awaitable[None]]:
        raise tornado.web.HTTPError(
            self._status_code,
            'request uri: %s',
            self.request.uri,
            reason=self._reason
        )


# Creating NotesRequestHandler
class NotesRequestHandler(BaseRequestHandler):
    async def get(self):
        '''
        GET request handler for notes request

        Returns:
            Status 200 along with the note object as response
        Raises:
            tornado.web.HTTPError [404] upon Exception
        '''
        try:
            all_notes = {}
            async for id_, note in self.service.get_notes():
                all_notes[id_] = note

            self.set_status(200)
            self.finish(all_notes)
        except Exception as e:
            raise tornado.web.HTTPError(404, reason=str(e))

    async def post(self):
        '''
        POST request handler for notes request

        Returns:
            Status 201 along with the note object as response
        Raises:
            tornado.web.HTTPError [404] upon Exception
            tornado.web.HTTPError [404] upon KeyError, Exception
        '''
        try:
            body = json.loads(self.request.body.decode('utf-8'))
            id = await self.service.create_note(body)
            note_uri = APP_VERSION + NOTES_ENTRY_URI_FORMAT_SR.format(id=id)
            self.set_status(201)
            self.set_header('Location', note_uri)
            self.finish()
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            )
        except Exception as e:
            raise tornado.web.HTTPError(404, reason=str(e))


# Creating NotesEntryRequestHandler
class NotesEntryRequestHandler(BaseRequestHandler):
    async def get(self, id):
        '''
        GET request handler for note entry

        Args:
            id: [str] Note ID

        Returns:
            Status 200 along with the note object as response
        Raises:
            tornado.web.HTTPError [404] upon KeyError, Exception
        '''
        try:
            response = await self.service.get_note(id)
            self.set_status(200)
            self.finish(response)
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))
        except Exception as e:
            raise tornado.web.HTTPError(404, reason=str(e))

    async def put(self, id):
        '''
        PUT request handler for note entry

        Args:
            id: [str] Note ID

        Returns:
            Status 204
        Raises:
            tornado.web.HTTPError [404] upon KeyError, Exception
            tornado.web.HTTPError [400] upon JSONDecodeError, TypeError
        '''
        try:
            body = json.loads(self.request.body.decode('utf-8'))
            await self.service.update_note(id, body)
            self.set_status(204)
            self.finish()
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            )
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))
        except Exception as e:
            raise tornado.web.HTTPError(404, reason=str(e))

    async def delete(self, id):
        '''
        DELETE request handler for note entry

        Args:
            id: [str] Note ID

        Returns:
            Status 204
        Raises:
            tornado.web.HTTPError [404] upon KeyError, Exception
        '''
        try:
            await self.service.delete_note(id)
            self.set_status(204)
            self.finish()
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))
        except Exception as e:
            raise tornado.web.HTTPError(404, reason=str(e))


def log_function(handler: tornado.web.RequestHandler) -> None:
    # https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings

    logger = getattr(handler, 'logger', logging.getLogger(LOGGER_NAME))

    if handler.get_status() < 400:
        level = logging.INFO
    elif handler.get_status() < 500:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logutils.log(
        logger,
        level,
        include_context=True,
        message='RESPONSE',
        status=handler.get_status(),
        time_ms=(1000.0 * handler.request.request_time())
    )

    logutils.clear_log_context()


def make_notesservice_app(
    config: Dict,
    debug: bool,
    logger: logging.Logger
) -> Tuple[NotesService, tornado.web.Application]:
    service = NotesService(config, logger)
    app = tornado.web.Application(
        [
            (
                APP_VERSION + NOTES_LIST_REGEX,
                NotesRequestHandler,
                dict(service=service, config=config, logger=logger)
            ),
            (
                APP_VERSION + NOTES_REGEX,
                NotesEntryRequestHandler,
                dict(service=service, config=config, logger=logger)
            )
        ],
        compress_response=True,  # compress textual responses
        log_function=log_function,  # log_request() uses it to log results
        serve_traceback=debug,  # it is passed on as setting to write_error()
        default_handler_class=DefaultRequestHandler,
        default_handler_args={
            'status_code': 404,
            'message': 'Unknown Endpoint',
            'logger': logger
        }
    )

    return service, app
