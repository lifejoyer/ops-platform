#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from OpsManage.utils.jenkins_api import JenkinsTools
from OpsManage.utils.kubernetes_api import K8sTools
from kubernetes import K8sDeployment
from kubernetes import K8sService
import json
import requests
import time



