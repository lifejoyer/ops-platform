#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from OpsManage.utils.jenkins_api import JenkinsTools
from OpsManage.utils.kubernetes_api import K8sTools
from kubernetes import K8sDeployment
from kubernetes import K8sService
from kubernetes import K8sSecret
import json
import requests
import time
import threading
import socket
import os
import telnetlib
from django.utils.encoding import smart_text
import re
import oss2
from kubernetes import K8sNode
from kubernetes import K8sPod

k = K8sTools(
    api_host='http://192.168.1.70:8000',
    token='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLTJtanRoIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI1MWY2MDkwYy1hNDhiLTExZTgtOGIzMC0wMDUwNTY5ZjI4YzYiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.fWFu0YoL-Wur3othdlg2X2H0oolDlJ4EHIOgBfa42Ivpp4KzNGuH3UwHZnRwp9C8n1Arc9meQanM3XwuVGfP73PFrNDITI6sj-07KBcQwnVsxS0aApCLoWbVmzttH6M2BohMGDOKIgcdeXaNNDvlv-tTBQ5uEFjfxP_AkR3yVko5hP-Wr2-fsex6XNhBz_AqcY1HdGKIeuWcPGlZMEIVG_ZgAFnv0PDAhYMvSYy43fKkS7rgfbO6kFCcOxk4ijaEPYGve15qigzRWfYvSk_BRDmLvBQ0MRdVPGIGZmela7fg8RYL0A4lhfweIm51NVeb5KJHj6QrdgewZaHJttt1bg',
    #token='eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWdiNTloIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI5OTFlMjViNi1hNmM3LTExZTgtOThiNy0wMDE2M2UxYWVlYjYiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.BPEr_gsUWP2dLXC-qwkYPjS65CzwZcLkum3rWzqZUJle8qCAEyxfYeQogEE-6MApfH9rd_XDusjzNKPgpRG3kUh3xrwSZm9V6_R7UXDZV-q82EQaJR8OynDEle8wXkJAu4-DlXHRf0ULhrk3eP7OPCj4qrcAcMaeDiCjMNzlSxOoEsj1lqquBGExdPHXg_zi-dvbBZoWKtZsPvvqHFJaZZ8Y8POBMykOZWjAvYK150553IGmqx0SsBmsTmHEWzZjTCpQxRSf1V4qEMMZspYokolVGPK9CUtnQHdmV1hr-xyFic30bNeiqAeCOrOtA56szqyNSvJf9qnnq5QmGd2kRA',
    namespace='default'
)


j = JenkinsTools(
    host='http://192.168.1.64:8080',
    username='admin',
    password='eeeaef4db71abc82790ac0c6290aee8f'
)


# res=j.create_deploy_job('aaaaaaa','echo hello world')

# print(k.create_pod(
#     name='tomcat-pod-test',
#     image='registry-vpc.cn-shanghai.aliyuncs.com/jhhjdk/tomcat8:v6',
#     env='test',
#     node={'zone':'u2licai-561'},
#     tol={'key':'dedicated','value':'u2licai-dubbo'}
# ))


# k.create_service(name='tomcat-pod-test',port='41000')
# k.del_service('tomcat-pod-test')
# k.create_service(name='dc-loan-service-test',port='20073',debug_port='20076')
#
# def test(a=None,b=None,**kwargs):
#     print(kwargs['node'] + '\n' + kwargs['secret'] +kwargs['tol']['key'] + kwargs['tol']['value'])
#
# test(node='node',secret='secret',tol={'key':'keys','value':'val'})



# resource = [{"ip": "192.168.1.64", "port": "22","username": "root","password": "1806cvpfKT8164"}]
# ANS = ANSRunner(resource)
#
# src = os.getcwd() + '/' + str("ping.txt")
# file_args = """src={src} dest={dest} owner={user} group={user} mode=755""".format(src="/root/jdk-7u80-linux-x64.rpm", dest="/tmp/jdk-7u80-linux-x64.rpm",user="root")
# sList = ["192.168.1.64"]
# ANS.run_model(host_list=sList, module_name="copy", module_args=file_args)
# result = ANS.handle_model_data(ANS.get_model_result(), 'copy', file_args)

# url='http://192.168.1.87:9200/upload'
# fo=open('ping.txt',mode='r')
# content=fo.readlines()
# data={
#     'token':'dspic',
#     'suffix':'.txt',
#     'data':'aaaaaa'
# }
#
# result=requests.post(url=url,data=json.dumps(data))
# print(result.content)
