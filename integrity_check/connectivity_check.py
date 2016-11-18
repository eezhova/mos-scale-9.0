import datetime
import json
import logging
import os

import pexpect

import integrity_check
from integrity_check import clients


neutron_client = clients.NeutronAuth.get_neutron_client()
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


def get_ips_of_instances(instance_ids, net_name, ip_type="fixed"):
    """Get instances' ip addresses.

    :param instance_ids: List of instance_ids.
    :param net_name: Name of the network to which ip addresses must belong to.
    :param ip_type: Type of ips to look for: fixed or floating.
           Defaults to fixed.
    :returns: Dict of ips with mapping "ip_addr": "type".
    """
    logging.info("Discovering {0} ips from network {1}".format(ip_type,
                                                               net_name))
    ips = {}
    for inst_id in instance_ids:
        instance = nova_client.servers.get(inst_id)
        for addr in instance.addresses[net_name]:
            if addr["OS-EXT-IPS:type"] == ip_type:
                ips[addr['addr']] = ip_type

    return ips


def get_network_id_by_name(net_name):
    """Get network id by its name.

    :param net_name: Name of a network
    :returns: Id of a network
    """
    networks = neutron_client.list_networks()['networks']
    for network in networks:
        if network['name'] == net_name:
            return network['id']


def ssh_and_ping(source_ip, dest_ips, namespace=None):
    """SSH to an instance and check connectivity to a number of ips.

    :param source_ip: IP address of an instance to SSH to.
    :param dest_ips: List of IP addresses to ping from instance.
    :param namespace: Name of namespace from which an SSH command should be
           issued. Used to SSH to an instance with fixed ip.
    :returns: None
    :raises: Exception if failed to SSH to an instance.
    """
    cmd = ["ssh"]
    prompt = '\$ '
    options = "-q -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null " \
              "-oPubkeyAuthentication=no -oConnectTimeout=10"

    if namespace:
        cmd.insert(0, "ip netns exec {}".format(namespace))
    cmd.append(options)
    cmd.append("{0}@{1}".format(integrity_check.VM_USERNAME, source_ip))
    command = " ".join(cmd)
    logging.debug("Running command: {}".format(command))

    try:
        child = pexpect.spawn(command)
        child.expect([pexpect.TIMEOUT, '[Pp]assword:'])
        child.sendline(integrity_check.VM_PASSWORD)
        child.expect([pexpect.TIMEOUT, prompt])
        for dest_ip in dest_ips:
            child.sendline("ping -c 4 -W 1 {0}".format(dest_ip))
            child.expect("(\d+)% packet loss")
            percent = int(child.match.group(1)) if child.match else -1
            if percent == 0:
                logging.info(
                    "Check connectivity from {0} to {1} successful.".format(
                        source_ip, dest_ip))
            else:
                logging.error("Check connectivity from {0} to {1} failed! "
                              "{2}% packet loss".format(source_ip,
                                                        dest_ip, percent))
        child.sendline("exit")
    except Exception:
        logging.error("Failed to ssh to instance with ip: {}".format(
            source_ip))
        return


def check_connectivity(ips, net_name):
    """Check connectivity between group of instances given their IPs.

    :param ips: List of dicts of ips with mapping "ip_addr": "type".
    :param net_name: Name of a network into which instances are plugged into.
    :returns: None
    """
    net_id = get_network_id_by_name(net_name)
    qdhcp_namespace = "qdhcp-" + net_id

    ips_to_ping = ips.keys()
    for ip in list(ips):
        namespace = None
        if ips[ip] == "fixed":
            namespace = qdhcp_namespace
        ips_to_ping.pop(0)
        dest_ips = ["8.8.8.8"] + ips_to_ping
        ssh_and_ping(ip, dest_ips, namespace)


def discover(save_file, net_name, sg_floating, sg_non_floating):
    """Discover IPs of control group's instances.

    :param save_file: A json file used to store instances' IPs.
    :param net_name: Name of the network in which instances are spawned.
    :param sg_floating: Name of a server group which instances
           have floating ips.
    :param sg_non_floating: Name of a server group which instances
           have only fixed ips.
    :returns: List of dicts of ips with mapping "ip_addr": "type".
    """
    if os.path.exists(save_file) and os.path.getsize(save_file) > 0:
        logging.info("Loading instances' ips from {}".format(save_file))
        with open(save_file, 'r') as f:
            ips = json.load(f)
    else:
        group1_inst = get_server_group_members(sg_floating)
        group2_inst = get_server_group_members(sg_non_floating)
        ips = {}
        floating_ips = get_ips_of_instances(group1_inst,
                                            net_name,
                                            ip_type="floating")
        ips.update(floating_ips)
        fixed_ips = get_ips_of_instances(group2_inst, net_name)
        ips.update(fixed_ips)
        with open(save_file, 'w') as f:
            json.dump(ips, f)
        logging.info("Saved instances' ips to {}".format(save_file))
    return ips


def get_parser():
    parser = integrity_check.get_parser()
    parser.add_argument('--sg-non-floating',
                        default=integrity_check.SERVER_GROUP_NON_FLOATING)
    parser.add_argument('--net', default=integrity_check.NETWORK_NAME)
    parser.add_argument('-s', '--save-file', required=True)
    return parser


def main():
    start_time = datetime.datetime.now()
    args = get_parser().parse_args()
    log_level = integrity_check.LOG_LEVELS[args.log_level]
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        level=log_level)
    ips = discover(args.save_file, args.net,
                   args.sg_floating, args.sg_non_floating)
    logging.debug("IPs to check: {}".format(ips))
    check_connectivity(ips, args.net)
    logging.info("Time: {}".format(datetime.datetime.now() - start_time))


if __name__ == "__main__":
    main()
