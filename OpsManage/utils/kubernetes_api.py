#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from kubernetes import K8sConfig
from kubernetes import K8sDeployment
from kubernetes import K8sNamespace
from kubernetes import K8sService
from kubernetes import K8sContainer
from kubernetes import K8sVolume
from kubernetes import K8sVolumeMount
from kubernetes import K8sSecret


class K8sTools(object):

    def __init__(self, api_host, token, namespace=None):
        self.api_host = api_host
        self.token = token
        self.namespace = namespace if namespace else 'default'

    @property
    def k8s_config(self):
        return K8sConfig(
            kubeconfig=None,
            api_host=self.api_host,
            token=self.token,
            namespace=self.namespace)

    def has_namespace(self, name):
        o = K8sNamespace(config=self.k8s_config, name=name)
        res = False
        for ds in o.list():
            if ds.name == name:
                res=True
                break
            else:
                continue
        return res

    def has_deployment(self, name):
        o = K8sDeployment(config=self.k8s_config, name=name)
        res = False
        for ds in o.list():
            if ds.name == name:
                res=True
                break
            else:
                continue
        return res

    def create_secret(self, name):
        data = {"auths":{"registry-vpc.cn-shanghai.aliyuncs.com":{"email":"test@163.com","auth":"authstring"}}}
        o=K8sSecret(config=self.k8s_config, name=name)
        o.create_image_pull_secret(name=name,
                                   config=self.k8s_config,
                                   data=data)
        return o.name

    def get_secret(self, name):
        secret = K8sSecret(config=self.k8s_config,name=name)
        return secret.get_model()

    def has_service(self, name):
        o = K8sService(config=self.k8s_config, name=name)
        res = False
        for ds in o.list():
            if ds.name == name:
                res=True
                break
            else:
                continue
        return res

    def create_namespace(self, name):
        o = K8sNamespace(config=self.k8s_config, name=name)
        return o.get() if self.has_namespace(name) else o.create()

    def create_deployment(self, name, image, env, rs=1, type='tomcat', port=8080,env_dict=False,mount_path=False):
        is_run = False
        if self.has_deployment(name): is_run=True
        container = K8sContainer(name=name, image=image)
        container.add_port(container_port=port)
        try:
            if isinstance(env_dict, dict) and env_dict:
                for k, v in env_dict.items(): container.add_env(name=str(k), value=str(v))
            container.add_env(name='ENVNAME', value=str(env))
        except Exception as ex:
            return "Error: 添加容器环境变量失败" + str(ex)
        try:
            mount_path = mount_path if mount_path else '/usr/local/tomcat/logs'
            if type == "tomcat":  container.add_env(name='aliyun_logs_'+name, value='stdout')
            else: container.add_env(name='aliyun_logs_'+name, value=mount_path + '/*.log')
            mount = K8sVolumeMount(name=name + '-logs', mount_path=mount_path)
            container.add_volume_mount(mount)
        except Exception as ex:
            return "Error: 容器数据卷添加失败" + str(ex)
        container.resources = {'requests': {"cpu": "200m", "memory": "1000M"}}
        deployment = K8sDeployment(
            config=self.k8s_config,
            name=name,
            replicas=rs)
        volume = K8sVolume(name=name + '-logs', type='hostPath')
        volume.path = "/acs/logs/" + self.namespace + '/' + name
        deployment.add_volume(volume)
        deployment.add_container(container)
        return deployment.update() if is_run else deployment.create()

    def create_service(self, name, port=None, debug_port=None):
        service = K8sService(config=self.k8s_config, name='svc-' + name)
        if port:
            service.add_port(name='web', port='8080', target_port='8080', node_port=str(port), protocol='TCP')
        if debug_port:
            service.add_port(name='debug', port='8087', target_port='8087', node_port=str(debug_port), protocol='TCP')
        service.add_selector(selector=dict(name=name))
        service.type = 'NodePort'
        is_run = False
        last_port = ""
        if self.has_service(name='svc-'+name):
            last_port = self.get_nodePort(name, "web")
            is_run = True
        if port and str(last_port) != str(port):
            if is_run:
                model = self.get_service(name)
                service.cluster_ip = model["spec"]["clusterIP"]
                service.model.metadata.resource_version=model['metadata']['resourceVersion']
                return service.update()
            else:
                return service.create()
        else:
            return False

    def get_service(self, name):
        service = K8sService(config=self.k8s_config, name='svc-' + name)
        return service.get_model()

    def get_deployment(self, name):
        o = K8sDeployment(config=self.k8s_config, name=name)
        return o.get_model()

    def del_service(self, name):
        service = K8sService(config=self.k8s_config, name='svc-' + name)
        return service.delete()

    def get_nodePort(self, name, port_name):
        ports = self.get_service(name)["spec"]['ports']
        res = False
        for p in ports:
            if p["name"] == port_name:
                res=p["nodePort"]
                break
            else:
                continue
        return res

    def del_namespace(self, name):
        o=K8sNamespace(config=self.k8s_config, name=name)
        return o.delete()

    def del_deployment(self, name):
        o=K8sDeployment(config=self.k8s_config,name=name)
        return o.delete()
