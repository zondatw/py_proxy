import logging

from proxy.server import ProxyServer

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)15s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    config = {
        "HOST_NAME": "127.0.0.1",
        "BIND_PORT": 8080,
    }
    ProxyServer(config).listen()

