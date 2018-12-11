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
from kubernetes import K8sNode
from kubernetes import K8sPod
import requests
import json


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
        data = {"auths":{"registry.cn-shanghai.aliyuncs.com":{"auth": "amluaHVoYW5nOnFKck4laDFzbjU4cA==", "email": "jinhuhang@aliyun.com"}}}
        secret=K8sSecret(config=self.k8s_config, name=name)
        secret.dockerconfigjson = data
        return secret.create()

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
            mount_path = mount_path if mount_path else '/opt/logs'
            if type == "tomcat":  container.add_env(name='aliyun_logs_'+name, value='stdout')
            elif type == "jar": container.add_env(name='aliyun_logs_'+name, value='stdout')
            else: container.add_env(name='aliyun_logs_'+name, value=mount_path + '/*.log')
            mount = K8sVolumeMount(name=name + '-logs', mount_path=mount_path)
            container.add_volume_mount(mount)
        except Exception as ex:
            return "Error: 容器数据卷添加失败" + str(ex)
        container.resources = {'requests': {"cpu": "300m", "memory": "800M"}}
        deployment = K8sDeployment(
            config=self.k8s_config,
            name=name,
            replicas=rs)
        volume = K8sVolume(name=name + '-logs', type='hostPath')
        volume.path = "/acs/logs/" + self.namespace + '/' + name
        # deployment.node_selector = {"node": "jhh-k8s-114"}
        # deployment.add_image_pull_secrets(secret=[{'name': 'aliyun-registry-jinhh'}])
        deployment.add_volume(volume)
        deployment.add_container(container)
        return deployment.update() if is_run else deployment.create()

    def create_service(self, name, port=None, debug_port=None):
        service = K8sService(config=self.k8s_config, name='svc-' + name)
        if port:
            service.add_port(name='web', port='8080', target_port='8080', node_port=str(port), protocol='TCP')
        if debug_port:
            service.add_port(name='debug', port='8787', target_port='8787', node_port=str(debug_port), protocol='TCP')
        service.add_selector(selector=dict(name=name))
        service.type = 'NodePort'
        is_run = False
        last_port = ""
        if self.has_service(name='svc-'+name):
            last_port = self.get_nodePort(name, "web")
            # last_debug_port = self.get_nodePort(name, 'debug')
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

    def get_node(self):
        o=K8sNode(config=self.k8s_config,name='default')
        return o.list()

    def get_pod(self, name, is_all=True):
        pod = K8sPod(config=self.k8s_config, name=name)
        if is_all: return pod.list()
        else: return pod.list(pattern=name)

    def had_pod(self, name):
        pod = K8sPod(config=self.k8s_config, name=name)
        res = False
        for ds in pod.list():
            if ds.name == name:
                res=True
                break
            else: continue
        return res

    def create_pod(self, name, image, env, type='tomcat', env_dict=False, mount_path=False, **kwargs):
        container = K8sContainer(name=name, image=image)
        container.add_port(container_port=8080)
        try:
            if isinstance(env_dict, dict) and env_dict:
                for k, v in env_dict.items(): container.add_env(name=str(k), value=str(v))
            container.add_env(name='ENVNAME', value=str(env))
        except Exception as ex:
            return "Error: 添加容器环境变量失败" + str(ex)
        try:
            mount_path = mount_path if mount_path else '/opt/logs'
            if type == "tomcat":  container.add_env(name='aliyun_logs_'+name, value='stdout')
            elif type == "jar": container.add_env(name='aliyun_logs_'+name, value='stdout')
            else: container.add_env(name='aliyun_logs_'+name, value=mount_path + '/*.log')
            mount = K8sVolumeMount(name=name + '-logs', mount_path=mount_path)
            container.add_volume_mount(mount)
        except Exception as ex:
            return "Error: 容器数据卷添加失败" + str(ex)
        container.resources = {'requests': {"cpu": "300m", "memory": "800M"}}
        volume = K8sVolume(name=name + '-logs', type='hostPath')
        volume.path = "/acs/logs/" + self.namespace + '/' + name
        pod = K8sPod(config=self.k8s_config, name=name)
        pod.add_container(container=container)
        pod.add_volume(volume=volume)
        if 'secret' in kwargs.keys(): pod.add_image_pull_secrets(secrets=[{'name': kwargs['secret']}])
        if 'node' in kwargs.keys(): pod.node_selector = kwargs['node']
        if 'tol' in kwargs.keys():
            pod.add_toleration(key=kwargs['tol']['key'], value=kwargs['tol']['value'],effect='NoSchedule')
        if self.had_pod(name): pod.delete()
        return pod.create()

    def delete_pod(self, name):
        pod = K8sPod(config=self.k8s_config, name=name)
        return pod.delete()


class kubeTools():

    def __init__(self, host, projectName, serviceName, api_user="", api_passwd=""):
        self.host = host
        self.namespace = projectName
        self.podname = serviceName
        self.api_user = api_user
        self.api_passwd = api_passwd

    def namespacesJson(self,name):
        data = '{ "kind": "Namespace", "apiVersion": "v1", "metadata": { "name": ' + name + '" } }'
        api="/api/v1/namespaces"
        return self.sendRequest("get",api)
        # pass

    # 更新k8s deployment
    def update_k8s_deployment(self, new_docker_img):
        if not new_docker_img:
            raise Exception("Error: docker image arguments input error!")
        api_url = self.host + "/apis/extensions/v1beta1/namespaces/" + self.namespace + "/deployments/" + self.podname
        return self.update_k8s_template(api_url, new_docker_img)

    # 发送http请求，用于更新、删除、创建、查询操作
    def sendRequest(self, api_url, request_method="get", data=""):
        headers = {'Content-Type': 'application/json'}
        if request_method == "get":
            r = requests.get(api_url).content.decode("utf-8")
            if "code" in json.loads(r).keys() and json.loads(r)["code"] == 404:
                raise Exception("Error: kubernetes中未找到该API的Pod")
            return r
        elif request_method == "put":
            return requests.put(api_url,data).content
        elif request_method == "post":
            return requests.post(api_url,data).content
        else:
            raise ValueError("Error: arguments input error !")

    # 初始化模板
    def init_new_template(self, api_url, new_docker_image):
        template_data = self.sendRequest(api_url, request_method="get")
        try:
            return template_data.replace(self.get_k8s_pod_container_image(api_url),
                                                     new_docker_image, 1)
        except:
            raise Exception("Error: 初始化k8s模板失败,程序退出！")

    # 更新模板操作
    def update_k8s_template(self, api_url, new_docker_img):
        template_data = self.init_new_template(api_url, new_docker_img)
        try:
            return requests.put(api_url, template_data).content.decode("utf-8")
        except:
            raise Exception("Error: kubernetes模板更新失败!")

    # 创建模板
    def create_k8s_template(self):
        pass

    # 获取pod的容器镜像
    def get_k8s_pod_container_image(self,api_url):
        t = self.sendRequest(request_method='get',api_url=api_url)
        return json.loads(t)["spec"]["template"]["spec"]["containers"][0]["image"]


class wayneTools():

    def __init__(self,host,token):
        self.host = host
        self.token = token

    def namespaces_list(self):
        api='/api/v1/namespaces/names?deleted=false'
        return self.send_request(api,'GET')

    def send_request(self,api,method='GET', data=''):
        headers = {
            'Authorization': 'Bearer '+ self.token,
            "content": "application/json"
        }
        url=self.host + api
        if method == 'GET':
            return requests.get(url, headers=headers).text
        elif method == "POST":
            return requests.post(url, data=data, headers=headers).text
        else:
            return False

    def get_k8s_cluster_name(self):
        api='/api/v1/clusters/names?deleted=false'
        cluster = json.loads(self.send_request(api, 'GET'))['data']
        data=[]
        for c in cluster: data.append(c.get('name'))
        return data

    def has_namespaces(self, name):
        namespaces_list = json.loads(self.namespaces_list())
        for n in namespaces_list['data']:
            if isinstance(n, dict):
                if n['name'] == name: return n
                else: continue
        return False

    def get_apps_list(self, namespaces):
        namespaces=self.has_namespaces(namespaces)
        api='/api/v1/namespaces/{id}/apps?pageNo=1&pageSize=100&sortby=-id&deleted=false&relate=namespace'.format(id=namespaces['id'])
        return self.send_request(api,'GET')

    def has_apps(self, namespaces, apps_name):
        namespaces=self.has_namespaces(namespaces)
        if not namespaces: return False
        api='/api/v1/namespaces/{id}/apps?pageNo=1&pageSize=100&sortby=-id&deleted=false&relate=namespace'.format(id=namespaces['id'])
        res = json.loads(self.send_request(api,'GET'))
        if not res['data']['list']: return False
        for apps in res['data']['list']:
            if apps['name'] == apps_name: return apps
            else: continue
        return False

    def has_deployment(self, namespaces, apps_name, name):
        app=self.has_apps(namespaces, apps_name)
        if not app: return False
        api='/api/v1/apps/{id}/deployments/names?appId={id}&deleted=false'.format(id=app['id'])
        deployment_list = json.loads(self.send_request(api,'GET'))
        if len(deployment_list['data']) < 1: return False
        for dep in deployment_list['data']:
            if dep['name'] == name: return dep
            else: continue
        return False

    def get_deployment_template(self):
        pass

    def create_namespaces(self, name):
        namespace=self.has_namespaces(name)
        if namespace: return namespace
        k8s_cluster = self.get_k8s_cluster_name()
        cluster_template={}
        for k8sName in k8s_cluster:
            cluster_template.update({
                k8sName: {
                    "resourcesLimit": {
                        "cpu": 0,
                        "memory": 0}
                }
            })
        temp_meta_data={"imagePullSecrets":[],
                       "env":[],
                       "clusterMeta":cluster_template,
                       "namespace":name
                       }
        template_data = {
            "metaDataObj": {
                "imagePullSecrets": [],
                "env": [],
                "clusterMeta": cluster_template,
                "namespace": name
            },
            "name": name,
            "metaData": json.dumps(temp_meta_data)
        }
        api="/api/v1/namespaces"
        return self.send_request(api,'POST',json.dumps(template_data))

    def create_apps(self, namespaces, name):
        app=self.has_apps(namespaces, name)
        if app: return app
        if not self.has_namespaces(namespaces): self.create_namespaces(namespaces)
        namespaceObj = self.has_namespaces(namespaces)
        data = {
            "namespace": {
                "metaDataObj":
                    {
                        "imagePullSecrets": [],
                        "env": [],
                        "clusterMeta": {}
                    },
                "id": namespaceObj['id']
            },
            "name": name,
            "description": name
        }
        api="/api/v1/namespaces/{id}/apps/".format(id=namespaceObj['id'])
        return self.send_request(api,'POST',json.dumps(data))

    def create_deployment(self, namespace, app_name, name):
        deployment=self.has_deployment(namespace,app_name,name)
        if deployment: return deployment
        if not self.has_apps(namespace, app_name): self.create_apps(namespace, app_name)
        app = self.has_apps(namespace, app_name)
        api="/api/v1/apps/{id}/deployments".format(id=app['id'])
        k8s_cluster=self.get_k8s_cluster_name()
        c1 = lambda k8s: [k for k in k8s if 'test' in k]
        c2 = lambda k8s: [k for k in k8s if 'prod' in k]
        if 'test' in app_name:  k8s_cluster_name=c1(k8s_cluster)
        else: k8s_cluster_name=c2(k8s_cluster)
        replicas={}
        for k in k8s_cluster_name: replicas[k]=1
        template_data={
            "replicas": replicas,
            "resources":{
                "cpuLimit":"4",
                "cpuRequestLimitPercent":"50%",
                "memoryLimit":"8",
                "memoryRequestLimitPercent":"100%",
                "replicaLimit":"1"
            }
        }
        data= {
            "metaData": json.dumps(template_data),
            "name": name,
            "description": name,
            "appId": app['id']
        }
        return self.send_request(api,'POST',json.dumps(data))

    def create_deployment_tpls(self):
        deployment = self.has_deployment(
            self._deployObject.get('namespace'),
            self._deployObject.get('appName'),
            self._deployObject.get('deployName'))
        if not deployment:
            result=self.create_deployment(
                self._deployObject.get('namespace'),
                self._deployObject.get('appName'),
                self._deployObject.get('deployName'))
            deployment=json.loads(result)['data']

        env_vars=[{"value": self._deployObject.get('project_env'),"name": "ENVNAME"},
              {"value": "stdout","name": "aliyun_logs_"+self.deployObject.get('deployName')}]
        env_vars.extend([self.deployObject.get('env_var')])
        template = {
            "apiVersion": "extensions/v1beta1",
            "kind": "Deployment",
            "metadata":
                {
                    "labels": {
                        "wayne-app": self._deployObject.get('appName'),
                        "wayne-ns": self._deployObject.get('namespace'),
                        "app": self._deployObject.get('deployName')
                    },
                    "name": self._deployObject.get('deployName')
                },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "wayne-app": self._deployObject.get('appName'),
                        "app": self._deployObject.get('deployName')
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "wayne-app": self._deployObject.get('appName'),
                            "wayne-ns": self._deployObject.get('namespace'),
                            "app": self._deployObject.get('deployName')
                        }
                    },
                    "spec": {
                        "containers": [
                            {"resources": {
                                "limits": {"memory": "2Gi", "cpu": "1"},
                                "requests": {
                                    "memory": "2Gi",
                                    "cpu": "0.5"}
                            },
                                "env": env_vars,
                                "envFrom": [],
                                "name": self._deployObject.get('deployName'),
                                "image": self._deployObject.get('image'),
                                "volumeMounts": [
                                    {
                                        "mountPath": "/opt/logs",
                                        "name": "application-logs"
                                    }
                                ]
                            }
                        ],
                        "volumes": [
                            {
                                "name": "application-logs",
                                "hostPath": {
                                    "path": self._deployObject.get('logPath')
                                }
                            }
                        ]
                    }
                },
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate":
                        {
                            "maxSurge": "20%",
                            "maxUnavailable": 1
                        }
                }
            }
        }

        data = {
            "description": self._deployObject.get('desc'),
            "deploymentId": deployment['id'],
            "template": json.dumps(template),
            "name": self._deployObject.get('deployName')
        }
        app=self.has_apps(self._deployObject.get('namespace'),self._deployObject.get('appName'))
        api = "/api/v1/apps/{appid}/deployments/tpls".format(appid=app['id'])
        self._deployObject.setdefault('appid',app['id'])
        self._deployObject.setdefault('deploymentId',deployment['id'])
        return self.send_request(api=api,method='POST',data=json.dumps(data))

    def run(self):
        data=json.loads(self.create_deployment_tpls)['data']
        data['metadata']['namespace']=self._deployObject.get('namespace')
        data['spec']['replicas'] = 1
        api='/kubernetes/apps/{appid}/deployments/{deploymentId}/tpls/{tplId}/clusters/{cluster}'.format(
            appid=self._deployObject.get('appid'),
            deploymentId=self._deployObject.get('deploymentId'),
            tplId=1,
            cluster=1)
        return self.send_request(api=api,method='POST',data=json.dumps(data))

    @property
    def deployObject(self):
        return self._deployObject

    @deployObject.setter
    def deployObject(self,obj={}):
        self._deployObject = obj
