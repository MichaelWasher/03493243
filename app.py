""" An example application for how to run commands in an existing Kubernetes Pod using Python"""

from kubernetes import client, config
from kubernetes.stream import stream
import os
import time

# Set the following values to affect the chosen Pod / Namespace
namespace_name = "openshift-console"
pod_name="console-846dd8cc46-4dm2h"
container_name="console"

## Setup the Kubernetes Authentication / Conext. Read it from the default KubeConfig
if 'KUBERNETES_PORT' in os.environ:
    config.load_incluster_config()
else:
    config.load_kube_config()

v1 = client.CoreV1Api()

def __main__():

    script = f"""
        env
    """ 
    
    pod_list = v1.list_namespaced_pod(namespace=namespace_name)
    target_pod = ""
    for pod in pod_list.items:
        if pod.metadata.name == pod_name:
            target_pod = pod
            break
    
    if target_pod == "":
        print(f"The Pod {pod_name} does not exist in the {namespace_name} Namespace.")
        exit(1)

    run_script_in_pod(target_pod=target_pod, target_container=container_name, script=script)
    
    print("I am complete and will sleep now to avoid a CrashLoopBackoff.")
    print("Sleeping")
    while(True):
        print("...")
        time.sleep(5)

def run_script_in_pod(target_pod, target_container, script):
    """

    Parameters
    ----------
    target_pod PodV1
    target_container String
    command String

    Returns
    -------
    Output from the command in a List
    """
    
    # Wait for Pod to be running
    wait_for_ready(target_pod)

    # Calling exec and waiting for response
    exec_command = [
        '/bin/sh',
        '-c', f"{script}"
    ]
    try:
        resp = stream(v1.connect_get_namespaced_pod_exec,
                      target_pod.metadata.name,
                      target_pod.metadata.namespace,
                      container=target_container,
                      command=exec_command,
                      stderr=True, stdin=False,
                      stdout=True, tty=False)
        print("Response: " + resp)
        return resp.splitlines(keepends=False)
    except client.exceptions.ApiException as e:
        print(e)
        return None


def wait_for_ready(pod):
    while True:
        resp = v1.read_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace)
        if resp.status.phase != 'Pending':
            break
        time.sleep(1)


__main__()
