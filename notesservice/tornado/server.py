# Importing modules
import asyncio
import argparse
import yaml
import tornado.web
from typing import Dict
from notesservice.service import NotesService
from notesservice.tornado.app import make_notesservice_app


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
):
    # Line commented due to lint issue
    # name = config['service']['name']
    loop = asyncio.get_event_loop()
    service.start()  # Start AddressBook service (business logic)
    # Bind http server to port
    http_server_args = {
        'decompress_request': True
    }
    http_server = app.listen(port, '', **http_server_args)
    try:
        loop.run_forever()        # Start asyncio IO event loop
    except KeyboardInterrupt:
        # signal.SIGINT
        pass
    finally:
        loop.stop()               # Stop event loop
        http_server.stop()        # stop accepting new http reqs
        loop.run_until_complete(  # Complete all pending coroutines
            loop.shutdown_asyncgens()
        )
        service.stop()            # stop service
        loop.close()              # close the loop


def main(args=parse_args()):

    config = yaml.load(args.config.read(), Loader=yaml.SafeLoader)

    # Creating note service tornado app
    notes_service, notes_app = make_notesservice_app(
        config, args.debug
    )

    run_server(
        app=notes_app,
        service=notes_service,
        config=config,
        port=args.port,
        debug=args.debug,
    )


if __name__ == '__main__':
    main()
