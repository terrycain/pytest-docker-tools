'''
This module contains tests of the 'orchestration' of dependent docker units.
If a container depends on an image and a container, and that container depends
on another container, and so on, then all the contains should be built in the
right order.
'''

from pytest_docker_tools import container_fixture, image_fixture, volume_fixture


container_fixture(
    'redis0',
    image='redis',
    environment={
        'MARKER': 'redis0-0sider',
    }
)

container_fixture(
    'mycontainer',
    image=image_fixture('foobar', 'tests/integration'),
    volumes={
        volume_fixture('myvolume'): {'bind': '/var/tmp'},
    },
    environment={
        'REDIS_IP': lambda redis0: redis0['ip'],
    }
)


def test_related_container_created(docker_client, mycontainer):
    ''' Creating mycontainer should pull in redis0 because we depend on it to calculate an env variable '''
    for container in docker_client.containers.list():
        if 'MARKER=redis0-0sider' in container.attrs['Config']['Env']:
            break
    else:
        assert False, 'redis0 not running'


def test_gets_related_container_ip(redis0, mycontainer):
    ''' The lambda we passed to environment should have been executed with the redis fixture value '''
    redis_ip_env = f'REDIS_IP={redis0["ip"]}'
    env = mycontainer['container'].attrs['Config']['Env']
    assert redis_ip_env in env


def test_gets_volume(myvolume, mycontainer):
    ''' The container should have a volume configured pointing at our fixturized volume '''
    for mount in mycontainer['container'].attrs['Mounts']:
        if mount['Name'] == myvolume.name:
            break
    else:
        assert False, 'Could not find attached volume'