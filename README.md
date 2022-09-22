# Notes app microservice

## 0. Get the source code

Get the source code for the tutorial:

``` bash
$ git clone https://github.com/btofficiel/notes-ms.git
$ cd notes-ms

$ tree -I 'venv|__pycache__|fs|dump|db|tmp'
.
├── LICENSE
├── README.md
├── configs
│   └── notesservice-local.yaml
├── data
│   ├── __init__.py
│   └── notes
│       ├── 27f5e84943e64876a0c8644a0695070a.json
│       └── 751e2c8ff2414955b3738db07da6d752.json
├── notesservice
│   ├── __init__.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── db_engines.py
│   │   ├── notes_db.py
│   │   └── store.db
│   ├── datamodel.py
│   ├── service.py
│   ├── tornado
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── server.py
│   └── utils
│       ├── __init__.py
│       ├── asyncutils.py
│       └── logutils.py
├── requirements.txt
├── run.py
├── schema
│   └── notes-v1.0.json
└── tests
    ├── __init__.py
    ├── integration
    │   ├── __init__.py
    │   ├── notesservice_test.py
    │   └── tornado_app_notesservice_handlers_test.py
    └── unit
        ├── __init__.py
        ├── datamodel_test.py
        ├── notes_data_test.py
        ├── notes_db_test.py
        └── tornado_app_handlers_test.py
```

The directory `notesservice ` is  for the source code of the service, and the directory `tests` is for keeping the tests.

## 1. Project Setup

Setup Virtual Environment:

``` bash
$ python3 -m venv .venv
$ source ./.venv/bin/activate
$ pip install --upgrade pip
$ pip3 install -r ./requirements.txt
```

### Code sanitation checks


You can run static type checker, linter, unit tests, and code coverage by either executing the tool directly or through `run.py` script. In each of the following, In each of the following, you can use either of the commands.

Static Type Checker:

``` bash
$ mypy ./notesservice ./tests

$ ./run.py typecheck
```

Linter:

``` bash
$ flake8 ./notesservice ./tests

$ ./run.py lint
```

Unit Tests:

``` bash
$ python -m unittest discover tests -p '*_test.py'

$ ./run.py test
```

Code Coverage:

``` bash
$ coverage run --source=notesservice --branch -m unittest discover tests -p '*_test.py'

$ coverage run --source=notesservice --branch ./run.py test
```

After running tests with code coverage, you can get the report:

``` bash
$ coverage report

Name                                  Stmts   Miss Branch BrPart  Cover
-----------------------------------------------------------------------
notesservice/__init__.py                  7      0      0      0   100%
notesservice/database/__init__.py         0      0      0      0   100%
notesservice/database/db_engines.py       6      0      2      0   100%
notesservice/database/notes_db.py       210      9     48      1    96%
notesservice/datamodel.py                70      5     24      5    89%
notesservice/service.py                  53      2      2      0    96%
notesservice/tornado/__init__.py          0      0      0      0   100%
notesservice/tornado/app.py             115     14     24      9    82%
notesservice/tornado/server.py           46     46      2      0     0%
notesservice/utils/__init__.py            0      0      0      0   100%
notesservice/utils/asyncutils.py          4      0      0      0   100%
notesservice/utils/logutils.py           28      0      6      0   100%
-----------------------------------------------------------------------
TOTAL                                   539     76    108     15    85%
```

You can also generate HTML report:

``` bash
$ coverage html
$ open htmlcov/index.html
```

If you are able to run all these commands, your project setup has no error and you are all set for coding.

---

## 2. Microservice

File `notesservice/service.py` has business logic for CRUD operations for the Notes app. This file is indpendent of any web service framework.
It currenly has just stubs with rudimentry implementation keeing notes in a dictionary. It is sufficint to implement and test the REST service endpoints.

[Tornado](https://www.tornadoweb.org/) is a framework to develop Python web/microservices. It uses async effectively to achieve high number of open connections. In this tutorial, we create a `tornado.web.Application` and add `tornado.web.RequestHandlers` in file `notesservice/tornado/app.py` to serve various API endpoints for this notes service. Tornado also has a rich framework for testing.

Web services return HTML back. In notesservice microservice, API data interface is JSON. We will examine key Tornado APIs of `Application`, `RequestHandler` and `tornado.testing` to develop it.

But first,let's explore our API and Data model


###  JSON Schema 

```json
{
	"$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Schema of a note taking app",
    "definitions": {
      "noteType": {
        "type": "string",
        "enum": ["personal", "work"]
      },
      "noteEntry": {
        "$id": "#noteEntry",
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "minLength": 32
          },
          "title": {
            "type": "string",
            "minLength": 1
          },
          "body": {
            "type": "string"
          },
          "updated_on": {
            "type": "number",
            "minimum": 0
          },
          "note_type": {
            "$ref": "#/definitions/noteType"
          }
       	},
        "required": ["title","body", "note_type"]
   	  }
    },
    "$ref": "#/definitions/noteEntry"
}
```

### API endpoints

#### Retrieve notes
<code>
GET /notes
</code>

<code>
GET /notes/{id}
</code>

#### Create a note
<code>
POST /notes
</code>

##### Request body
```json
{
	"title": "Note title",
	"body": "Note body",
	"note_type": "personal/work"
}
```

The type for the above properties would be:-

* **titile** : *string* 
* **body** : *string*
* **note_type** : *string* [Needs to be either "personal" or "work" ]

#### Update a note

<code>
PUT /notes/{id}
</code>

##### Request body
```json
{
	"title": "Note title",
	"body": "Note body",
	"note_type": "personal/work"
}
```

The type for the above properties would be:-

* **titile** : *string* 
* **body** : *string*
* **note_type** : *string* [Needs to be either "personal" or "work" ]

#### Delete note
<code>
DELETE /notes/{id}
</code>


### SQL setup
```sql
CREATE TABLE notes (
	id varchar(32) PRIMARY KEY,
	title varchar NOT NULL,
	body varchar NOT NULL DEFAULT '',
	note_type varchar CHECK( note_type IN ('personal', 'work') ) NOT NULL,
	updated_on bigint DEFAULT 0
)
```
	

Now, to run our service, enter the following command

``` bash
$ PYTHONPATH=./ python3 notesservice/tornado/server.py --port 8080 --config ./configs/notesservice-local.yaml --debug

```

Let's run operations on our microservice now.

#### Create a note
```bash
curl -i -X POST http://localhost:8080/v1/notes -d '{"title": "Note", "body": "Note Body", "note_type": "work"}'

HTTP/1.1 201 Created
Server: TornadoServer/6.0.3
Content-Type: text/html; charset=UTF-8
Date: Wed, 21 Sep 2022 12:38:55 GMT
Location: /v1/notes/6aad2682a0184b0fb930f7f3153f030f
Content-Length: 0
Vary: Accept-Encoding
```

We can see the id in the 'Location' header, so we just copy the id to retrieve our created note

#### Retrieving a note
```bash
curl -i -X GET http://localhost:8080/v1/notes/6aad2682a0184b0fb930f7f3153f030f

HTTP/1.1 200 OK
Server: TornadoServer/6.0.3
Content-Type: application/json; charset=UTF-8
Date: Wed, 21 Sep 2022 12:41:13 GMT
Etag: "d161a60d17471537b8be3fda56c0dfa48d41e72d"
Content-Length: 127
Vary: Accept-Encoding

{"id": "6aad2682a0184b0fb930f7f3153f030f", "title": "Note", "body": "Note Body", "note_type": "work", "updated_on": 1663763935}
```

We can also update an existing note via

```bash
curl -i -X PUT http://localhost:8080/v1/notes/6aad2682a0184b0fb930f7f3153f030f -d '{"title": "Updated Note", "body": "Note Body", "note_type": "work"}'

HTTP/1.1 204 No Content
Server: TornadoServer/6.0.3
Date: Wed, 21 Sep 2022 12:43:40 GMT
Vary: Accept-Encoding
```

We can get a list of all notes by running this curl command

```bash
curl -i -X GET http://localhost:8080/v1/notes/

HTTP/1.1 200 OK
Server: TornadoServer/6.0.3
Content-Type: application/json; charset=UTF-8
Date: Thu, 22 Sep 2022 15:12:23 GMT
Etag: "c576dbe088662f761c03e79bbae39e779271b98a"
Content-Length: 2135
Vary: Accept-Encoding

{"2f7f4199c4b64dd3baa5f2be5b492334": {"id": "2f7f4199c4b64dd3baa5f2be5b492334", "title": "Updated Note via REST", "body": "This is my second note", "note_type": "work", "updated_on": 1663835055}, "5b83f264629b4fd493efdef3e3e8f9f3": {"id": "5b83f264629b4fd493efdef3e3e8f9f3", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859511}, "fcc0eb3d499d4f4e8c8257913ebc8ae1": {"id": "fcc0eb3d499d4f4e8c8257913ebc8ae1", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859512}, "39fa70384b1f4548bb442dfdf6c16637": {"id": "39fa70384b1f4548bb442dfdf6c16637", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859512}, "7523f6682b5b420eb3025b53f246a72d": {"id": "7523f6682b5b420eb3025b53f246a72d", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859512}, "54e03e1839f044b0a78fe9a8c30f4235": {"id": "54e03e1839f044b0a78fe9a8c30f4235", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859512}, "a333fb727a8c443cb1b8d7ac1096de2d": {"id": "a333fb727a8c443cb1b8d7ac1096de2d", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859513}, "07e658b4e8554bc8955c63ce62a96c44": {"id": "07e658b4e8554bc8955c63ce62a96c44", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859513}, "0f9a988ccc9c44e59a55778eac884723": {"id": "0f9a988ccc9c44e59a55778eac884723", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859513}, "81ef2e289b5d42919550efc38c7fdd5c": {"id": "81ef2e289b5d42919550efc38c7fdd5c", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859513}, "3284a85329c64f388af6a647fb8ae4ea": {"id": "3284a85329c64f388af6a647fb8ae4ea", "title": "Updated Note via SQL", "body": "This is my second note", "note_type": "work", "updated_on": 1663859513}}
```

At last, we can delete the note we have created.

```bash

curl -i -X DELETE http://localhost:8080/v1/notes/6aad2682a0184b0fb930f7f3153f030f

HTTP/1.1 204 No Content
Server: TornadoServer/6.0.3
Date: Wed, 21 Sep 2022 12:47:33 GMT
Vary: Accept-Encoding
```

Effective logs can cut down diagnosis time and facilitate monitoring and altering.

### Log Format

[Logfmt](https://pypi.org/project/logfmt/) log format consists of *key-value* pairs.
It offers good balance between processing using standard tools and human readibility.

### Canonical Logs

Emiting one canonical log line](https://brandur.org/canonical-log-lines) for each request makes manual inspection easier.
Assigning and logging a *request id* to each request, and passing that id to all called service helps correlate logs across services.
The *key-value* pairs for the log are stored in a [task context](https://github.com/Skyscanner/aiotask-context), which is maintained across asyncio task interleaving.

### Log Configuration

Logging are useful in diagnosing services, more so when async is involved. Python has a standard [logging](https://docs.python.org/3/library/logging.html) package, and its documentation includes an excellent [HOWTO](https://docs.python.org/3/howto/logging.html) guide and [Cookbook](https://docs.python.org/3/howto/logging-cookbook.html). These are rich source of information, and leave nothoing much to add. Following are some of the best practices in my opinion:

- Do NOT use ROOT logger directly throgh `logging.debug()`, `logging.error()` methods directly because it is easy to overlook their default behavior.
- Do NOT use module level loggers of variety `logging.getLogger(__name__)` because any complex project will require controlling logging through configuration (see next point). These may cause surprise if you forget to set `disable_existing_loggers` to false or overlook how modules are loaded and initialized. If use at all, call `logging.getLogger(__name__)` inside function, rather than outside at the beginning of a module.
- `dictConfig` (in `yaml`) offers right balance of versatility and flexibility compared to `ini` based `fileConfig`or doing it in code. Specifying logger in config files allows you to use different logging levels and infra in prod deployment, stage deployments, and local debugging (with increasingly more logs).

Sending logs to multiple data stores and tools for processing can be controled by a [log configuration](https://docs.python.org/3/library/logging.config.html). Each logger has a format and multiple handlers can be associated with a logger. Here is a part of `configs/notesservice-local.yaml`:

``` yaml
logging:
  version: 1
  formatters:
    brief:
      format: '%(asctime)s %(name)s %(levelname)s : %(message)s'
    detailed:
      format: 'time="%(asctime)s" logger="%(name)s" level="%(levelname)s" file="%(filename)s" lineno=%(lineno)d function="%(funcName)s" %(message)s'
  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: brief
      stream: ext://sys.stdout
    file:
      class : logging.handlers.RotatingFileHandler
      level: DEBUG
      formatter: detailed
      filename: /tmp/notesservice-app.log
      backupCount: 3
  loggers:
    notesservice:
      level: DEBUG
      handlers:
        - console
        - file
      propagate: no
    tornado.access:
      level: DEBUG
      handlers:
        - file
    tornado.application:
      level: DEBUG
      handlers:
        - file
    tornado.general:
      level: DEBUG
      handlers:
        - file
  root:
    level: WARNING
    handlers:
      - console
```

Notice that this configuration not just defines a logger `notesservice` for this service, but also modifies behavior of Tornado's general logger. There are several pre-defined [handlers](https://docs.python.org/3/library/logging.handlers.html). Here the SteamHandler and RotatingFileHandler are being used to write to console and log files respectively.

### Tornado

Tornado has several hooks to control when and how logging is done:

- [`log_function`](https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings): function Tornado calls at the end of every request to log the result.
- [`write_error`](https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write_error): to customize the error response. Information about the error is added to the log context.
- [`log_exception`](): to log uncaught exceptions. It can be overwritten to log in logfmt format.

### Log Inspection

**Start the server:**

It will show the console log:

``` bash
$ python3 notesservice/tornado/server.py --port 8080 --config ./configs/notesservice-local.yaml --debug

2022-09-21 15:29:02,243 notesservice INFO : message="STARTING" service_name="Notes" port=8080
```

**Watch the logs:**

``` bash
$ tail -f /tmp/notesservice-app.log

time="2022-09-21 15:29:52,088" logger="notesservice" level="DEBUG" file="logutils.py" lineno=56 function="log" req_id="c297ded2a4454d7cbf3cb21aec114b24" method="GET" uri="/v1/notes" ip="127.0.0.1" message="REQUEST"
```

**Send a request:**

```bash
$ curl -i -X POST http://localhost:8080/v1/notes -d '{"title": "Note", "body": "Note Body", "note_type": "work"}'

HTTP/1.1 201 Created
Server: TornadoServer/6.0.3
Content-Type: text/html; charset=UTF-8
Date: Wed, 21 Sep 2022 12:38:55 GMT
Location: /v1/notes/6aad2682a0184b0fb930f7f3153f030f
Content-Length: 0
Vary: Accept-Encoding
```

The console log will show brief log entries:

``` log
2020-03-17 12:56:32,784 notesservice INFO : req_id="e6cd3072530f46b9932946fd65a13779" method="POST" uri="/v1/tasks" ip="::1" message="RESPONSE" status=201 time_ms=1.2888908386230469
```

The log file will show logfmt-style one-line detailed canonical log entries:

``` log
time="2022-09-21 15:56:05,291" logger="notesservice" level="DEBUG" file="logutils.py" lineno=56 function="log" req_id="f9845edaab90435abcc0312eca43336e" method="GET" uri="/v1/notes" ip="127.0.0.1" message="REQUEST" service_name="notesservice"
```




