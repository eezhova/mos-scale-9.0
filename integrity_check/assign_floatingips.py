import logging

import integrity_check
from integrity_check import clients


nova_client = clients.NovaAuth.get_nova_client()


def get_server_group_members(name):
    """Get a list of ServerGroup members by its name.

    :param name: Name of a server group
    :returns: List of ids of server group members
    """

    logging.info("Discovering members of group {}".format(name))
    sg_members = []

    for sg in nova_client.server_groups.list():
        if sg.name == name:
            sg_members.extend(sg.members)
            break

    return sg_members


def assign_floating_ips(instances):
    """Create and assign floating ips to instances.

    :param instances: List of ids of instances.
    :returns: None
    """
    for inst_id in instances:
        fl_ip = nova_client.floating_ips.create()
        logging.info("Created floating ip with address: {}". format(fl_ip.ip))
        nova_client.servers.add_floating_ip(inst_id, address=fl_ip)
        logging.info("Associated floating ip {0} with instance {1}".format(
            fl_ip.ip, inst_id))


def cleanup_floating_ips(instances):
    """Delete floating ips from instances.

    :param instances: List of ids of instances.
    :returns: None
    """
    floating_ips = nova_client.floating_ips.list()
    for fl_ip in floating_ips:
        if fl_ip.instance_id in instances:
            logging.info("Deleting floating ip {}".format(fl_ip.ip))
            nova_client.floating_ips.delete(fl_ip)


def get_parser():
    parser = integrity_check.get_parser()
    parser.add_argument(
        '--cleanup', action='store_true',
        help='Remove floating ips associations and delete them.')
    return parser


def main():
    args = get_parser().parse_args()
    log_level = integrity_check.LOG_LEVELS[args.log_level]
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        level=log_level)
    group1_inst = get_server_group_members(args.sg_floating)
    if not args.cleanup:
        assign_floating_ips(group1_inst)
    else:
        cleanup_floating_ips(group1_inst)


if __name__ == '__main__':
    main()
