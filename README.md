# maas-sdk-python

[![Master Build Status](https://secure.travis-ci.org/miracl/maas-sdk-python.png?branch=master)](https://travis-ci.org/miracl/maas-sdk-python?branch=master)
[![Master Coverage Status](https://coveralls.io/repos/miracl/maas-sdk-python/badge.svg?branch=master&service=github)](https://coveralls.io/github/miracl/maas-sdk-python?branch=master)

* **category**:    SDK
* **copyright**:   2016 MIRACL UK LTD
* **license**:     ASL 2.0 - http://www.apache.org/licenses/LICENSE-2.0
* **link**:        https://github.com/miracl/maas-sdk-python

## Description

Python version of the Software Development Kit (SDK) for MPin-As-A-Service (MAAS).


# Setup

Run `python setup.py` for setup. It uses python-setuptools.

Some dependencies require additional system packages to be installed.
For Ubuntu 14.04 the dependencies are:

* `build-essential` (for compiling code in dependencies)
* `python-dev` or `python3-dev` (depending on python version used)
* `libssl-dev`
* `libffi-dev`
* `python-setuptools`

## Installation

`python setup.py install`

## Development setup

`python setup.py develop` will install the package using a symlink to the source code.

## Tests

To run tests, use `python setup.py test`.


# Miracl APIs

## Details and usage

All interaction with the APIs happen through a `MiraclClient` object. Each
application needs to construct a `MiraclClient` instance.

Miracl API requires a map-like object for storing state and additional data (which
should be preserved between api calls). In this document it is called
`session`.

### Initialization
To start using Miracl APIs, a `MiraclClient` should be initialized. This can be done
when needed or at application startup. This instance can be shared between
threads and is thread-safe.

```
client = MiraclClient(
    client_id="CLIENT_ID",
    secret="SECRET",
    redirect_uri="REDIRECT_URI")
```

`CLIENT_ID` and `SECRET` can be obtained from Miracl (unique per
application). `REDIRECT_URI` is the URI of your application end-point that will be
responsible for obtaining a token. It should be the same as is registered in the Miracl
system for this client ID.

It is possible to override default issuer with the `issuer` parameter.

### Status check and user data

To check if the user session has a token use `client.is_authorized(session)`. You can
 request additional user data with `client.get_email(session)` and
 `client.get_user_id(session)`. Both methods cache results into `session`. If
 `None` is returned, the token has expired and the client needs to be authorized once
 more to access the required data.

Use `client.clear_user_info(session)` to drop cached user data (e-mail and
user id).

Use `client.clear_user_info(session, including_auth=True)` to clear user
authorization status.

### Authorization flow

The authorization flow depends on the `mpad.js` browser library. To show the login button:

* Insert a div with a distinct ID where the login button is to appear
* Use `client.get_authorization_request_url(session)` to generate the authorization URL
* At the end of the page body load `mpad.js` with parameters `data-authurl`
(authorization URL) and `data-element` (login button ID)

```
<script src="https://dd.cdn.mpin.io/mpad/mpad.js" data-authurl="{{ auth_url }}" data-element="btmpin"></script>
```

After user
interaction with the login button the user will be sent to the `redirect_uri` defined at
creation of `MiraclClient` object.

To complete authorization pass the query string received at the `redirect_uri` to
`client.validate_authorization(session,query_string)`. This method will return
`None` if the user is denied authorization and a token if authorization has succeeded. The token
is preserved in `session` so there is no need to save the token elsewhere.

### Problems and exceptions

Each call to `MiraclClient` can raise `MiraclError`. This contains `message` and
 `exception` (optional, can be `None`). Usually `MiraclError` is raised when
 the API call can't continue; it is best to redirect the user to the error page if
 `MiraclError` is raised. `MiraclError` can contain helpful messages when
 debugging.

`MiraclClient` uses the Python logging package and can be configured to be verbose
for debugging purposes. Below is a sample configuration for logging that will
output all debug information from `MiraclClient`:

```
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
```

Log levels used:

* `DEBUG` for all requests and retrieved data
* `INFO` for initial provider configuration
* `ERROR` when exception is raised

## Samples

In the `samples` directory, `miracl.json` contains the app credentials config. Replace `CLIENT_ID`, `CLIENT_SECRET` and `REDIRECT_URI` with valid data for your app. The sample app can then be run.

The redirect URI for this sample is `http://127.0.0.1:5000/c2id` if run locally.

### Flask

The flask sample app depends on `python-flask`.

## Docker

Configure the sample app with your credentials (see Samples above) then run docker

`docker build --tag=miracl/flasksdk .`

`docker run -d -p 5000:5000 miracl/flasksdk`

Open the app at url `http://127.0.0.1:5000/` 
