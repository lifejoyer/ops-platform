#!/usr/bin/env python  
# _#_ coding:utf-8 _*_ 
import json
from celery import task
from OpsManage.utils import base
from OpsManage.models import (Log_Project_Config,Global_Config,Email_Config,Deploy_Record)
from django.contrib.auth.models import User
from channels import Group as CGroups
import time

# @task
def recordProject(project_user,project_id,project_name,project_content,project_branch=None):
    try:
        config = Global_Config.objects.get(id=1)
        if config.project == 1:
            Log_Project_Config.objects.create(
                                      project_id = project_id,
                                      project_user = project_user,
                                      project_name = project_name,
                                      project_content = project_content,
                                      project_branch = project_branch
                                      )
        return True
    except Exception as e:
        print(e)
        return False


def recordProjectDeploy(user,project_name,service_name,image_name,run_env,is_online=1):
    try:
        Deploy_Record.objects.create(
            user=user,
            project_name=project_name,
            service_name=service_name,
            image_name=image_name,
            image_version=str(image_name).split(':')[-1],
            run_env=run_env,
            is_online=is_online,
            create_time=str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        )
    except Exception as e:
        print(e)
        return False
