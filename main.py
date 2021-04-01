import argparse
import logging

from proxy.server import ProxyServer

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)15s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", help="Domain name", default="127.0.0.1", type=str)
    parser.add_argument("-p", "--port", help="Bind port", default=8080, type=int)

    args = parser.parse_args()

    config = {
        "HOST_NAME": args.domain,
        "BIND_PORT": args.port,
    }
    ProxyServer(config).listen()

