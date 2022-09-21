# Notes app microservice

## 0. Get the source code

Get the source code for the tutorial:

``` bash
$ git clone https://github.com/btofficiel/notes-ms.git
$ cd notes-ms

$ tree -I 'venv|__pycache__'
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
│   ├── service.py
│   └── tornado
│       ├── __init__.py
│       ├── app.py
│       └── server.py
├── requirements.txt
├── run.py
└── tests
    ├── __init__.py
    ├── integration
    │   ├── __init__.py
    │   └── tornado_app_notesservice_handlers_test.py
    └── unit
        ├── __init__.py
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

Name                               Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------------------
notesservice/service.py               38      3      2      1    90%
notesservice/tornado/__init__.py       0      0      0      0   100%
notesservice/tornado/app.py           80     12     12      5    79%
notesservice/tornado/server.py        34     34      2      0     0%
--------------------------------------------------------------------
TOTAL                                152     49     16      6    65%
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
It currenly has just stubs with rudimentry implementation keeing tasks in a dictionary. It is sufficint to implement and test the REST service endpoints.

[Tornado](https://www.tornadoweb.org/) is a framework to develop Python web/microservices. It uses async effectively to achieve high number of open connections. In this tutorial, we create a `tornado.web.Application` and add `tornado.web.RequestHandlers` in file `taskservice/tornado/app.py` to serve various API endpoints for this tasks service. Tornado also has a rich framework for testing.

Web services return HTML back. In todoList microservice, API data interface is JSON. We will examine key Tornado APIs of `Application`, `RequestHandler` and `tornado.testing` to develop it.

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
Content-Type: text/html; charset=UTF-8
Date: Wed, 21 Sep 2022 12:44:35 GMT
Etag: "2ae3ff4769065aa36a855a95aed79b02e27afbda"
Content-Length: 418
Vary: Accept-Encoding

[
{"id": "754a747361cc403aa74e6d8b37981caa", "title": "Updasdate note", "body": "This is my second note", "note_type": "work", "updated_on": 1663763135}, 
{"id": "4724b8eea0514c24b603b07634674085", "title": "Note", "body": "Note Body", "note_type": "work", "updated_on": 1663763859}, 
{"id": "6aad2682a0184b0fb930f7f3153f030f", "title": "Updated Note", "body": "Note Body", "note_type": "work", "updated_on": 1663764220}
]
```

At last, we can delete the note we have created.

```bash

curl -i -X DELETE http://localhost:8080/v1/notes/6aad2682a0184b0fb930f7f3153f030f

HTTP/1.1 204 No Content
Server: TornadoServer/6.0.3
Date: Wed, 21 Sep 2022 12:47:33 GMT
Vary: Accept-Encoding
```






