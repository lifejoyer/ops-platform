#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from OpsManage.utils.jenkins_api import JenkinsTools
from OpsManage.utils.kubernetes_api import K8sTools
from kubernetes import K8sDeployment
from kubernetes import K8sService
import json
import requests
import time


k = K8sTools(
    api_host='http://192.168.1.70:8080',
    token='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLXRtNWs2Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI3Nzk0ODg3Yi04MTFjLTExZTgtOWFiMy0wMDUwNTY5ZjI4YzYiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.NQiym-NZL5-wKm8VX3jfcPoW2LBPRcVXFUjlsNU2PwDMGYJ0E4q8KGsQUPKpyYsQzFH1PYbRKrcMmyqaKfSmrEP8jXRlUfQC7l-Iryt0yyUTfKdj44drPHi_k2LwIv2dxnLOXZDS6_ZdrpWNZT0sdcCOChpf1ltfrJFSlfZNNR_sK6LBi4plUhO4nCBYdZZOYMKPi9rwe-xcsAgrR2erU61q2iq0SZ2EPDvX4igq2ReizLPHGEwi4Lq4tOgykIrZ6H9UuwuvTHqElrw-W6ob-D4eKQH4Ut5CGR0EtR5bUnMlgJ6ZtbtDQGI-NbI92WvjYrXqEzg93_WGfW-LaTXP5Q',
    namespace='suixindai'
)



r=k.del_namespace('suixindai')

# r=k.create_service('dc-loan-app-test')
# print(r)

# project_env_var=None
# mount_path=None
# res=k.create_deployment(name='dc-loan-app-test',
#                   image='docker.jhh.com/suixindai-dc-loan-app:1533867959',
#                   env='test',
#                   type='jar')
# print(res)

# j = JenkinsTools(
#     host="http://192.168.1.64:8080",
#     username="admin",
#     password="eeeaef4db71abc82790ac0c6290aee8f"
# )
#

