import os

from paste.deploy import loadapp
from cheroot import wsgi

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    wsgi_app = loadapp('config:converta.ini', relative_to='.')
    host = '0.0.0.0', port
    server = wsgi.Server(host, wsgi_app, numthreads=10, request_queue_size=200)
    server.start()
