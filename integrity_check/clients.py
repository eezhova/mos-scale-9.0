import os

from keystoneauth1.identity import v2 as v2_client
from keystoneauth1 import session
from neutronclient.neutron import client as neutron_client
from novaclient import api_versions
from novaclient import client as nova_client

NEUTRON_VERSION = '2.0'
NOVA_VERSION = '2.1'
_SESSION = None


def get_session():
    """Initializes a Keystone session."""

    global _SESSION
    if not _SESSION:

        auth_url = os.getenv('OS_AUTH_URL',
                             'http://192.168.0.2:5000/v2.0')
        if "v2.0" not in auth_url.split('/'):
            auth_url += "v2.0"

        kwargs = {'auth_url': auth_url,
                  'username': os.getenv('OS_USERNAME', 'admin'),
                  'password': os.getenv('OS_PASSWORD', 'admin'),
                  'tenant_name': os.getenv('OS_TENANT_NAME', 'admin'),
                  }

        kc = v2_client.Password(**kwargs)
        _SESSION = session.Session(
            auth=kc, verify=False)

    return _SESSION


class NovaAuth(object):
    nova_client = None

    @classmethod
    def get_nova_client(cls, region=None, service_name=None, endpoint=None,
                        endpoint_type='publicURL', insecure=False,
                        cacert=None):
        """Create nova client object.

        :param region: The region of the service
        :param service_name: The name of the nova service in the catalog
        :param endpoint: The endpoint of the service
        :param endpoint_type: The type of the endpoint
        :param insecure: Turn off certificate validation
        :param cacert: CA Cert file path
        :return: a Nova Client object.
        :raises Exception: if the client cannot be created
        """

        if not region:
            region = os.getenv('OS_REGION_NAME', 'RegionOne')
        if not cls.nova_client:
            kwargs = {'region_name': region,
                      'session': get_session(),
                      'endpoint_type': endpoint_type,
                      'insecure': insecure}
            if service_name:
                kwargs['service_name'] = service_name
            if endpoint:
                kwargs['endpoint_override'] = endpoint
            if cacert:
                kwargs['cacert'] = cacert

            cls.nova_client = nova_client.Client(
                version=api_versions.APIVersion(NOVA_VERSION), **kwargs)
        return cls.nova_client


class NeutronAuth(object):
    neutron_client = None

    @classmethod
    def get_neutron_client(cls, region=None, service_name=None, endpoint=None,
                           endpoint_type='publicURL', insecure=False,
                           ca_cert=None):
        """Create neutron client object.

        :param region: The region of the service
        :param service_name: The name of the neutron service in the catalog
        :param endpoint: The endpoint of the service
        :param endpoint_type: The endpoint_type of the service
        :param insecure: Turn off certificate validation
        :param ca_cert: CA Cert file path
        :return: a Neutron Client object.
        :raises Exception: if the client cannot be created
        """

        if not region:
            region = os.getenv('OS_REGION_NAME', 'RegionOne')
        if not cls.neutron_client:
            kwargs = {'region_name': region,
                      'session': get_session(),
                      'endpoint_type': endpoint_type,
                      'insecure': insecure}
            if service_name:
                kwargs['service_name'] = service_name
            if endpoint:
                kwargs['endpoint_override'] = endpoint
            if ca_cert:
                kwargs['ca_cert'] = ca_cert

            cls.neutron_client = neutron_client.Client(
                NEUTRON_VERSION, **kwargs)
        return cls.neutron_client
