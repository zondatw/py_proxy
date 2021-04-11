import argparse
import logging

from .server import ProxyServer

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="url", default="127.0.0.1", type=str)
    parser.add_argument("-p", "--port", help="Bind port", default=8080, type=int)
    parser.add_argument(
        "--allowed_access",
        help="if using it, could only access what you set. "
             "when allow all port, please input '*'",
        action="append",
        nargs=2,
        metavar=("ip/mask", "port"),
        default=[],
    )
    parser.add_argument(
        "--blocked_access",
        help="if using it, will block access what you set. "
             "when block all port, please input '*'. "
             "Note: this setting has higher priority than allowed_access",
        action="append",
        nargs=2,
        metavar=("ip/mask", "port"),
        default=[],
    )
    parser.add_argument(
        "--forwarding",
        help="forward a to b",
        action="append",
        nargs=4,
        metavar=("original ip/mask", "original port", "destination ip", "destination port"),
        default=[],
    )
    parser.add_argument(
        "--lb_frontend",
        help="Load balancing frontend",
        nargs=2,
        metavar=("frontend ip/mask", "frontend port"),
        default=[],
    )
    parser.add_argument(
        "--lb_backend",
        help="Load balancing backend",
        action="append",
        nargs=3,
        metavar=("backend ip/mask", "backend port", "access rate"),
        default=[],
    )

    args = parser.parse_args()

    config = {
        "url": args.url,
        "port": args.port,
        "allowed_accesses": args.allowed_access,
        "blocked_accesses": args.blocked_access,
        "forwarding": args.forwarding,
        "load_balancing": {
            "frontend": args.lb_frontend,
            "backend": args.lb_backend,
        }
    }
    logger.debug(f"Proxy setting: {config}")
    ProxyServer(**config).listen()

