import argparse
import logging


NETWORK_NAME = "integrity_network"
SERVER_GROUP_FLOATING = "nova_server_group_floating"
SERVER_GROUP_NON_FLOATING = "nova_server_group_non_floating"

VM_USERNAME = "cirros"
VM_PASSWORD = "cubswin:)"

LOG_LEVELS = {"info": logging.INFO,
              "debug": logging.DEBUG}


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-level', choices=['debug', 'info'],
                        default='info')
    parser.add_argument('--sg-floating', default=SERVER_GROUP_FLOATING)
    return parser
