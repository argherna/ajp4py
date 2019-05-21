=======
ajp4py
=======

********
Overview
********

ajp4py is an AJP library. It's intent is similar to the Requests
library in that a usable API is presented so that making AJP
reqeusts to servers like Tomcat can be done in an simple
programmatic way.

Sample usage for a GET request to a locally hosted Tomcat servlet
container on port 8009:

.. code-block:: python

  >>> import ajp4py as ajp_requests
  >>> r = ajp_requests.get('ajp://localhost/docs/index.html')
  >>> r.status_code
  200
  >>> 'Apache Tomcat User Guide' in r.content
  True


The other methods supported by AJP are supported, see `ajp4py.api`.
