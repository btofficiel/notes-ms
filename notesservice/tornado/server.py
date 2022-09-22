# Importing modules

import aiotask_context as context  # type: ignore
import argparse
import asyncio
import logging
import logging.config
from typing import Dict
import yaml

import tornado.web

from notesservice.service import NotesService
from notesservice.tornado.app import make_notesservice_app
from notesservice import LOGGER_NAME
import notesservice.utils.logutils as logutils


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Run Address Book Server'
    )

    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=8080,
        help='port number for %(prog)s server to listen; '
        'default: %(default)s'
    )

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='turn on debug logging'
    )

    parser.add_argument(
        '-c',
        '--config',
        required=True,
        type=argparse.FileType('r'),
        help='config file for %(prog)s'
    )

    args = parser.parse_args(args)
    return args


def run_server(
    app: tornado.web.Application,
    service: NotesService,
    config: Dict,
    port: int,
    debug: bool,
    logger: logging.Logger
):
    name = config['service']['name']
    loop = asyncio.get_event_loop()
    loop.set_task_factory(context.task_factory)

    # Start Notes service
    service.start()

    # Bind http server to port
    http_server_args = {
        'decompress_request': True
    }
    http_server = app.listen(port, '', **http_server_args)
    logutils.log(
        logger,
        logging.INFO,
        message='STARTING',
        service_name=name,
        port=port
    )

    try:
        # Start asyncio IO event loop
        loop.run_forever()
    except KeyboardInterrupt:
        # signal.SIGINT
        pass
    finally:
        service.stop()
        loop.stop()
        logutils.log(
            logger,
            logging.INFO,
            message='SHUTTING DOWN',
            service_name=name
        )
        http_server.stop()
        # loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logutils.log(
            logger,
            logging.INFO,
            message='STOPPED',
            service_name=name
        )


def main(args=parse_args()):
    '''
    Starts the Tornado server serving Notes on the given port
    '''

    config = yaml.load(args.config.read(), Loader=yaml.SafeLoader)

    # First thing: set logging config
    logging.config.dictConfig(config['logging'])
    logger = logging.getLogger(LOGGER_NAME)

    notes_service, notes_app = make_notesservice_app(
            config,
            args.debug,
            logger
    )

    run_server(
        app=notes_app,
        service=notes_service,
        config=config,
        port=args.port,
        debug=args.debug,
        logger=logger
    )


if __name__ == '__main__':
    main()
