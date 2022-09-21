# Importing modules

import tornado.web
from typing import (
    Any,
    Awaitable,
    Dict,
    Optional,
)
import traceback
import json
from notesservice.service import NotesService

NOTES_LIST_REGEX = r'/notes/?'
NOTES_REGEX = r'/notes/(?P<id>[a-zA-Z0-9-]+)/?'
APP_VERSION = r'/v1'
NOTES_ENTRY_URI_FORMAT_SR = r'/notes/{id}'


# Creating a base request handler class
class BaseRequestHandler(tornado.web.RequestHandler):
    # Setting up initializetion hook
    def initialize(
        self,
        service: NotesService,
        config: Dict
    ):
        self.service = service
        self.config = config

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        self.set_header(
            'Content-Type', 'application/json; charset=UTF-8'
        )
        body = {
            'method': self.request.method,
            'uri': self.request.path,
            'code': status_code,
            'message': self._reason
        }
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, send a traceback
            trace = '\n'.join(traceback.format_exception(
                *kwargs['exc_info']
            ))
            body['trace'] = trace
        self.finish(body)


class DefaultRequestHandler(BaseRequestHandler):
    def initialize(self, status_code, message):
        self.set_status(status_code, reason=message)

    def prepare(self) -> Optional[Awaitable[None]]:  # type: ignore
        raise tornado.web.HTTPError(
            self._status_code, reason=self._reason
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
            response = await self.service.get_notes()
            self.set_status(200)
            self.finish(json.dumps(response))
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


def make_notesservice_app(
    config: Dict,
    debug: bool
):
    service = NotesService(config)
    app = tornado.web.Application(
        [
            (
                APP_VERSION + NOTES_LIST_REGEX,
                NotesRequestHandler,
                dict(service=service, config=config)
            ),
            (
                APP_VERSION + NOTES_REGEX,
                NotesEntryRequestHandler,
                dict(service=service, config=config)
            )
        ],
        compress_response=True,
        serve_traceback=debug,
        default_handler_class=DefaultRequestHandler,
        default_handler_args={
            'status_code': 404,
            'message': 'Unknown Endpoint'
        }
    )

    return service, app
