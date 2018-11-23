#!/usr/bin/env python  
# _*_ coding:utf-8 _*_
import uuid,os
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from OpsManage.models import (Project_Assets,Server_Assets,Project_Config,
                                Project_Number,Log_Project_Config,Service_Assets,Assets,
                              Jenkins_Assets,K8s_Assets, Deploy_Record,RunEnv_Assets)
from OpsManage.utils.git import GitTools
from OpsManage.utils.svn import SvnTools
from OpsManage.utils import base
from OpsManage.utils import chatbot
from OpsManage.data.DsRedisOps import DsRedis
from OpsManage.utils.ansible_api_v2 import ANSRunner
from OpsManage.utils.jenkins_api import JenkinsTools
from OpsManage.utils.kubernetes_api import K8sTools
from django.contrib.auth.models import User,Group
from OpsManage.views.assets import getBaseAssets
from orders.models import Order_System
from OpsManage.tasks.deploy import (recordProject,recordProjectDeploy)
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from OpsManage.utils.logger import logger
from OpsManage import settings
from OpsManage.views import assets
from dao.assets import AssetsSource
import json
import time
import math
from django.db.models import Q
from django.forms.models import model_to_dict

@login_required()
@permission_required('OpsManage.can_add_project_config',login_url='/noperm/')
def deploy_add(request):
    if request.method == "GET":
        serverList = Server_Assets.objects.all()
        groupList = Group.objects.all()
        return render(request,'deploy/deploy_add.html',{"user":request.user,"groupList":groupList,
                                                        'baseAssets':getBaseAssets(),"serverList": serverList,
                                                        "project_dir":settings.WORKSPACES})
    elif request.method == "POST":
        k8s_id=request.POST.get("k8s_id")
        if not k8s_id: k8s_id=K8s_Assets.objects.all()[0].id
        ipList=request.POST.get("project_server")
        try:
            proAssets = Project_Assets.objects.get(id=request.POST.get('project_id'))
            jenAssets = Jenkins_Assets.objects.get(id=request.POST.get('jenkins_id'))
            k8sAssets = K8s_Assets.objects.get(id=k8s_id)
            svcAssets = Service_Assets.objects.get(id=request.POST.get('service_id'))
        except Exception as ex:
            return JsonResponse({'msg':"部署项目添加失败: {ex}".format(ex=ex),"code":500,'data':[]})
        try:
            project_env = request.POST.get('project_env')
            project_audit_group = request.POST.get('project_audit_group') if project_env == 'prod' else None
            project = Project_Config.objects.create(
                                                    project = proAssets,
                                                    project_env = project_env,
                                                    project_local_command = request.POST.get('project_local_command'),
                                                    project_dir = request.POST.get('project_dir'),
                                                    project_uuid = uuid.uuid4(),
                                                    project_status = 0,
                                                    project_repo_dir=request.POST.get('project_repo_dir')+project_env+'/',
                                                    project_address=request.POST.get('project_address'),
                                                    project_repo_user = request.POST.get('project_repo_user'),
                                                    project_repo_passwd = request.POST.get('project_repo_passwd'),
                                                    project_branch = request.POST.get('project_branch'),
                                                    project_type=request.POST.get('project_type'),
                                                    project_repertory = request.POST.get('project_repertory'),
                                                    project_category = request.POST.get('project_category'),
                                                    jenkins=jenAssets,
                                                    k8s=k8sAssets,
                                                    service=svcAssets,
                                                    project_service_port = request.POST.get('project_service_port'),
                                                    project_debug_port=request.POST.get('project_debug_port'),
                                                    project_env_var=request.POST.get('project_env_var'),
                                                    project_mount_path=request.POST.get('project_mount_path'),
                                                    project_audit_group=project_audit_group,
                                                    project_replication=request.POST.get('project_replication', 1)
                                                    )
            recordProject(project_user=str(request.user),project_id=project.id,project_name="增加部署项目",project_content="添加代码发布项目")
        except Exception as ex:
            logger.error(msg="部署项目添加失败: {ex}".format(ex=ex))
            return JsonResponse({'msg':"部署项目添加失败: {ex}".format(ex=ex),"code":500,'data':[]})
        if ipList:
            for sid in ipList.split(','):
                try:
                    server = Server_Assets.objects.get(id=sid)
                    Project_Number.objects.create(server=server.ip,
                                                  project=project)
                except Exception as ex:
                    project.delete()
                    logger.error(msg="部署项目添加失败: {ex}".format(ex=ex))
                    return JsonResponse({'msg':"部署项目添加失败: {ex}".format(ex=ex),"code":500,'data':[]})
    return JsonResponse({'msg':"部署项目添加成功","code":200,'data':[]})
    
@login_required()
@permission_required('OpsManage.can_change_project_config',login_url='/noperm/')
def deploy_modf(request,pid): 
    try:
        project = Project_Config.objects.select_related().get(id=pid)
        k8s = K8s_Assets.objects.all()
        jenkins = Jenkins_Assets.objects.all()
        serverList = Server_Assets.objects.all()
        tagret_server=Project_Number.objects.filter(project=project)
    except Exception as ex:
        logger.error(msg="修改项目失败: {ex}".format(ex=ex))
        return render(request,'deploy/deploy_modf.html',{"user":request.user,
                                                         "errorInfo":"修改项目失败: {ex}".format(ex=ex)},
                                )  
    if request.method == "GET":
        serviceList = Service_Assets.objects.filter(project=project.project)
        groupList = Group.objects.all()
        server = [ s.server for s in tagret_server ]
        for ds in serverList:
            if ds.ip in server:ds.count = 1
            else:ds.count = 0
        return render(request,'deploy/deploy_modf.html',{"user":request.user,"project":project,"k8s":k8s,
                                                         "jenkins":jenkins,"groupList":groupList,"serviceList":serviceList,
                                                         "serverList": serverList,"server":tagret_server},
                                                         )
    elif request.method == "POST":
        k8s_id=request.POST.get("k8s_id")
        if not k8s_id: k8s_id=K8s_Assets.objects.all()[0].id
        ipList = request.POST.get('project_server', None)
        try:
            project_env = request.POST.get('project_env')
            project_audit_group = request.POST.get('project_audit_group') if project_env == 'prod' else None
            Project_Config.objects.filter(id=pid).update(
                                                    project_env = project_env,
                                                    project_type = request.POST.get('project_type'),
                                                    service_id = request.POST.get('service_id'),
                                                    project_repertory = request.POST.get('project_repertory'), 
                                                    project_address = request.POST.get('project_address'),
                                                    project_repo_dir = request.POST.get('project_repo_dir'),
                                                    project_local_command = request.POST.get('project_local_command'),
                                                    project_dir = request.POST.get('project_dir'),
                                                    project_repo_user = request.POST.get('project_repo_user'),
                                                    project_repo_passwd = request.POST.get('project_repo_passwd'),
                                                    project_branch=request.POST.get('project_branch'),
                                                    project_category=request.POST.get('project_category'),
                                                    jenkins_id=request.POST.get('jenkins_id'),
                                                    k8s_id=k8s_id,
                                                    project_service_port=request.POST.get('project_service_port'),
                                                    project_debug_port=request.POST.get('project_debug_port'),
                                                    project_env_var=request.POST.get('project_env_var'),
                                                    project_mount_path=request.POST.get('project_mount_path'),
                                                    project_audit_group=project_audit_group,
                                                    project_replication=request.POST.get('project_replication', 1)
                                                    )
            recordProject(project_user=str(request.user),project_id=pid,project_name="修改部署项目",project_content="部署项目修改")
        except Exception as ex:
            logger.error(msg="部署项目修改失败: {ex}".format(ex=ex))
            return JsonResponse({'msg':"部署项目修改失败: {ex}".format(ex=ex),"code":500,'data':[]})
        if ipList:
            tagret_server_list = [s.server for s in tagret_server]
            postServerList = []
            for sid in ipList.split(','):
                try:
                    server = Server_Assets.objects.get(id=sid)
                    postServerList.append(server.ip)
                    if server.ip not in tagret_server_list:
                        Project_Number.objects.create(server=server.ip,project=project)
                except Exception as ex:
                    logger.error(msg="部署项目修改失败: {ex}".format(ex=ex))
                    return JsonResponse({'msg': "部署项目修改失败: {ex}".format(ex=ex), "code": 500, 'data': []})
                    # 清除目标主机 -
            delList = list(set(tagret_server_list).difference(set(postServerList)))
            for ip in delList:
                Project_Number.objects.filter(project=project, server=ip).delete()
    return JsonResponse({'msg':"部署项目修改成功","code":200,'data':[]})         
        
@login_required()
@permission_required('OpsManage.can_read_project_config',login_url='/noperm/')
def deploy_list(request):
    userInfo = User.objects.get(username=request.user)
    if userInfo.is_superuser == 1:
        deployList = Project_Config.objects.all()
    else: deployList = Project_Config.objects.filter(project_env__startswith = "test")
    for ds in deployList:
        ds.number = Project_Number.objects.filter(project=ds)
    uatProject = Project_Config.objects.filter(project_env="uat").count()
    testProject = Project_Config.objects.filter(project_env__startswith = "test").count()
    prodProject = Project_Config.objects.filter(project_env="prod").count()
    return render(request,'deploy/deploy_list.html',{"user":request.user,"totalProject":deployList.count(),
                                                         "deployList":deployList,"uatProject":uatProject,"baseAssets": assets.getBaseAssets(),
                                                         "testProject":testProject,"prodProject":prodProject,"userInfo":userInfo},
                              )

@login_required()
@permission_required('OpsManage.can_read_project_config',login_url='/noperm/')
def deploy_list_v2(request):
    userInfo = User.objects.get(username=request.user)
    if userInfo.is_superuser == 1:
        deployList = Project_Config.objects.all()
    else: deployList = Project_Config.objects.filter(project_env__startswith = "test")
    for ds in deployList:
        ds.number = Project_Number.objects.filter(project=ds)
    uatProject = Project_Config.objects.filter(project_env="uat").count()
    testProject = Project_Config.objects.filter(project_env__startswith = "test").count()
    prodProject = Project_Config.objects.filter(project_env="prod").count()
    serviceList=Service_Assets.objects.all()
    data={}
    data["server"]=serviceList
    data["env"] = RunEnv_Assets.objects.all()
    # serviceList.env = RunEnv_Assets.objects.all()
    return render(request,'deploy/deploy_list2.html',{"user":request.user,"totalProject":deployList.count(),"serviceList":serviceList,
                                                         "deployList":deployList,"uatProject":uatProject,"baseAssets": assets.getBaseAssets(),
                                                         "testProject":testProject,"prodProject":prodProject,"userInfo":userInfo},
                              )

@login_required()
@permission_required('OpsManage.can_read_project_config', login_url='/noperm/')
def deploy_search(request):
    userInfo = User.objects.get(username=request.user)
    ProjectFieldsList = [n.name for n in Project_Config._meta.fields]
    if request.method == "POST":
        ProjectIntersection = list(set(request.POST.keys()).intersection(set(ProjectFieldsList)))
        DeployList = []
        data = dict()
        # 格式化查询条件
        for (k, v) in request.POST.items():
            if v is not None and v != u'':
                data[k] = v

        if len(ProjectIntersection) > 0:
            assetsData = dict()
            for a in ProjectIntersection:
                for k in data.keys():
                    if k.find(a) != -1:
                        assetsData[k] = data[k]
                        data.pop(k)

            if userInfo.is_superuser == 1:
                DeployList.extend(Project_Config.objects.filter(**assetsData))
            else:
                if "project_env" in data.keys():
                    DeployList.extend(Project_Config.objects.filter(**assetsData))
                else:
                    DeployList.extend(Project_Config.objects.filter(project_env__startswith="test", **assetsData))

        # baseAssets = getBaseAssets()
        dataList = []
        for a in DeployList:
            project = a.project.project_name
            service = a.service.service_name

            if a.project_env == 'prod':
                status = '''<button  type="button" class="btn active btn-info">请走工单</button>'''
            else:
                if a.project_status == 0:
                    status = '''<button type="button" class="btn btn-outline btn-warning" onclick="initProject(this,'{service}',{id})">编译打包</button>'''.format(service=a.service.service_name,id=a.id)
                else:
                    status = '''<button type="button" class="btn btn-outline btn-success" onclick="initProject(this,'{service}',{id})">编译打包</button>'''.format(service=a.service.service_name,id=a.id)
            if a.project_env == 'test':
                env = '''<span class="label label-success">测试环境</span>'''
            elif a.project_env == 'test2':
                env = '''<span class="label label-success">测试环境2</span>'''
            elif a.project_env == 'uat':
                env = '''<span class="label label-warning">灰度环境</span>'''
            elif a.project_env == 'prod':
                env = '''<span class="label label-danger">生产环境</span>'''
            opt = ''' 
                     <a href="/deploy_mod/{id}"><button  type="button" title="修改资料" class="btn btn-default"><abbr title="修改资料"><i class="glyphicon glyphicon-edit"></i></abbr></button></a>
                 '''.format(id=a.id)
            if a.project_env == 'prod':
                opt += '''
                       <a href="/order/deploy/apply/{id}"><button  type="button" class="btn btn-default"><abbr title="部署申请"><i class="fa fa-play-circle-o"></i></abbr></button></a>
                    '''.format(id=a.id)
            else:
                if a.project_status == 1:
                    opt += '''
                       <a href="/deploy_run/{id}"  title="部署"><button  type="button" class="btn btn-default"><abbr title="部署"><i class="fa fa-play-circle-o"></i></abbr></button></a>
                    '''.format(id=a.id)
                else:
                    opt += '''
                        <button  type="button" class="btn btn-default" title="提示"
							data-container="body" data-toggle="popover" data-placement="top"
							data-content="请先打包编译" data-html="true"><i class="fa fa-play-circle-o"></i></button>
                    '''
                # opt += '''
                # 	<div class="btn-group-vertical">
					# 	<div class="btn-group-vertical">
					# 		<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
                #                 <abbr title="分支控制"><i class="fa fa-github"></i></abbr>
					# 			<span class="caret"></span>
					# 		</button>
					# 		<ul class="dropdown-menu">
					# 		    <li><a href="javascript:" onclick="projcectVersion(this,'branch',{id},'create')">创建Branch</a></li>
					# 		    <li role="presentation" class="divider"></li>
					# 			<li><a href="javascript:" onclick="projcectVersion(this,'branch',{id},'delete')">删除Branch</a></li>
					# 			<li><a href="javascript:" onclick="projcectVersion(this,'tag',{id},'delete')">删除Tag</a></li>
					# 		</ul>
					# 	</div>
					# </div>
                # '''.format(id=a.id)
            opt += '''
                <button  type="button" class="btn btn-default" onclick="deleteProject(this,{id})"><abbr title="删除"><i class="glyphicon glyphicon-trash"></i></abbr></button>
            '''.format(id=a.id)
            dataList.append(
                {'ID': str(a.id),
                 '产品线': project,
                 '服务模块': service,
                 '项目环境': env,
                 '服务端口': str(a.project_service_port),
                 '仓库分支': str(a.project_branch),
                 '编译状态': status,
                 '操作': opt}
            )
            #"详情": '',
        return JsonResponse({'msg': "数据查询成功", "code": 200, 'data': dataList, 'count': 0})

# @login_required()
# @permission_required('OpsManage.can_read_project_config', login_url='/noperm/')
def new_deploy_search(request):
    ServiceFieldsList = [ n.name for n in Service_Assets._meta.fields]
    if request.method == "POST":
        ServiceIntersection = list(set(request.POST.keys()).intersection(set(ServiceFieldsList)))
        data = dict()
        # 格式化查询条件
        for (k, v) in request.POST.items():
            if v is not None and v != u'':
                data[k] = v

        if len(ServiceIntersection) > 0:
            assetsData = dict()
            for a in ServiceIntersection:
                for k in data.keys():
                    if k.find(a) != -1:
                        assetsData[k] = data[k]
                        data.pop(k)
            DeployList=Service_Assets.objects.filter(**assetsData)
        else:
            DeployList = Service_Assets.objects.all()

        dataList = []
        for a in DeployList:
            if a.service_pom_path == "1":
                opt='''<span class="label label-success">模块编译</span>'''
            else:
                opt='''<span class="label label-warning">全局编译</span>'''
            dataList.append(
                {'ID': str(a.id),
                 '产品线': a.project.project_name,
                 '服务模块': a.service_name,
                 '服务类型': str(a.service_type),
                 '编译类型': opt,
                 '仓库地址': a.service_repo_address,
                 '仓库用户': a.service_repo_user}
            )
            #"详情": '',
        return JsonResponse({'msg': "数据查询成功", "code": 200, 'data': dataList, 'count': 0})

@login_required()
@permission_required('OpsManage.can_change_project_config',login_url='/noperm/')
def deploy_init(request,pid):      
    if request.method == "POST": 
        project = Project_Config.objects.select_related().get(id=pid)
        if project.project_repertory == 'git': version = GitTools()
        elif project.project_repertory == 'svn': version = SvnTools()
        version.mkdir(dir=project.project_repo_dir)
        if project.project_type == 'yes': version.mkdir(dir=project.project_dir)
        result = version.clone(url=project.project_address, dir=project.project_repo_dir, user=project.project_repo_user, passwd=project.project_repo_passwd)
        if result[0]>0: return JsonResponse({'msg':result[1],"code":500,'data':[]})
        else:
            Project_Config.objects.filter(id=pid).update(project_status = 1)  
            recordProject(project_user=str(request.user),project_id=project.id,project_name=project.service.service_name,project_content="初始化项目")
            return JsonResponse({'msg':"初始化成功","code":200,'data':[]})


@login_required()
def deploy_version(request,pid): 
    try:
        project = Project_Config.objects.select_related().get(id=pid)
        if project.project_repertory == 'git': version = GitTools()
    except:
        return render(request,'deploy/deploy_version.html',{"user":request.user,
                                                         "errorInfo":"项目不存在，可能已经被删除."}, 
                                  )      
    if request.method == "POST":
        try:
            project = Project_Config.objects.get(id=pid)
            if project.project_repertory == 'git':version = GitTools()
            elif project.project_repertory == 'svn':version = SvnTools()
        except:
            return JsonResponse({'msg':"项目资源不存在","code":403,'data':[]}) 
        if project.project_status == 0:return JsonResponse({'msg':"请先初始化项目","code":403,'data':[]}) 
        if request.POST.get('op') in ['create','delete','query','histroy']:
            if  request.POST.get('op') == 'create':
                if request.POST.get('model') == 'branch':result = version.createBranch(path=project.project_repo_dir,branchName=request.POST.get('name'))
                elif request.POST.get('model') == 'tag':result = version.createTag(path=project.project_repo_dir,tagName=request.POST.get('name'))
            elif request.POST.get('op') == 'delete':
                if request.POST.get('model') == 'branch':result = version.delBranch(path=project.project_repo_dir,branchName=request.POST.get('name'))
                elif request.POST.get('model') == 'tag':result = version.delTag(path=project.project_repo_dir,tagName=request.POST.get('name')) 
            elif request.POST.get('op') == 'query':
                if project.project_model == 'branch':
                    result = version.log(path=project.project_repo_dir,bName=request.POST.get('name'),number=50)
                    return JsonResponse({'msg':"操作成功","code":200,'data':result}) 
                else:result = version.tag(path=project.project_repo_dir)
            elif request.POST.get('op') == 'histroy':
                result = version.show(path=project.project_repo_dir,branch=request.POST.get('project_branch'),cid=request.POST.get('project_version',None))
                return JsonResponse({'msg':"操作成功","code":200,'data':"<pre> <xmp>" + result[1].replace('<br>','\n') + "</xmp></pre>"}) 
        else:return JsonResponse({'msg':"非法操作","code":500,'data':[]})
        if result[0] > 0:return JsonResponse({'msg':result[1],"code":500,'data':[]})
        else:return JsonResponse({'msg':"操作成功","code":200,'data':[]})


@login_required()
@permission_required('OpsManage.can_change_project_config',login_url='/noperm/')
def deploy_compile(request,pid):
    if request.method == "POST":
        service_list=[]
        project = Project_Config.objects.select_related().get(id=pid)
        if project.service.service_pom_path=="1":
            service_list.append(project.service.service_name)
        else:
            service_group = Service_Assets.objects.filter(project_id=project.project_id,service_pom_path="0")
            for s in service_group:
                service_list.append(s.service_name)
        service_list=";".join(service_list)
        try:
            jenkins = JenkinsTools(
                host=project.jenkins.jenkins_host,
                username=project.jenkins.jenkins_user,
                password=project.jenkins.jenkins_token)
        except Exception as ex:
            logger.error(msg="项目部署失败: {ex}".format(ex=ex))
            return JsonResponse({'msg': str("jenkins连接失败"), "code": 500, 'data': []})
            # for p in project_group:
            #     service_list.append(p[0]["service_id"])
        project_name = str(project.project.project_english_name)
        service_name = str(project.service.service_name)
        if project.service.service_pom_path == "1":
            job_name = project_name + '-' + service_name + "-compile-" + project.project_env
        else:
            job_name = project_name + '-compile-' + project.project_env
        lock_id = project.project_uuid + "-compile"
        if DsRedis.OpsProject.get(redisKey=lock_id+"-locked") is None:
            DsRedis.OpsProject.set(redisKey=lock_id + "-locked", value=request.user)
            DsRedis.OpsDeploy.delete(lock_id)
            try:
                jenkins.create_credential(
                    username=str(project.project_repo_user),
                    password=str(project.project_repo_passwd),
                    c_id=str(job_name))
                DsRedis.OpsDeploy.lpush(lock_id,
                                        data="[Jenkins create credential %s" % job_name)
                time.sleep(1)
                cmd = "jhhTool2 --mode={mode} --project={project} --service={service} --work_dir={work_dir} --build_type={build_type}".format(mode="pack",
                                                                                 project="'"+project_name+"'",
                                                                                 service="'"+service_list+"'",
                                                                                 work_dir="'/opt'",
                                                                                 build_type=str(project.service.service_type))
                result = jenkins.create_job(str(job_name),
                                                   str(project.project_branch),
                                                   str(job_name),
                                                   str(project.project_address),
                                                   str(cmd))
                DsRedis.OpsDeploy.lpush(lock_id,
                                        data="Jenkins create jobs {job} info: {info}".format(
                                            job=job_name, info=result))
                build_number = str(jenkins.get_next_build_number(job_name))
                DsRedis.OpsDeploy.lpush(lock_id,
                                        data="Jenkins build job {name} info: job number {info}".format(
                                            name=job_name, info=str(build_number)))
                result = jenkins.build_job(job_name)
                DsRedis.OpsDeploy.lpush(lock_id, data="Jenkins build job {name} info: {info}".format(
                    name=job_name, info=result))
                time.sleep(1)
            except Exception as ex:
                DsRedis.OpsProject.delete(redisKey=lock_id + "-locked")
                return JsonResponse({'msg': "jenkins create job fail " + str(ex), "code": 500, 'data': []})

            # 判断jenkins构建是否运行完毕
            try:
                building = True
                DsRedis.OpsDeploy.lpush(lock_id, data="Jenkins job building, wait a minute...... ")
                while building:
                    build_status = jenkins.is_building(job_name, int(build_number))
                    if build_status:
                        time.sleep(1)
                    else:
                        building = False
            except Exception as ex:
                DsRedis.OpsProject.delete(redisKey=lock_id + "-locked")
                return JsonResponse({'msg': "jenkins获取构建状态失败 "+str(ex), "code": 500, 'data': []})

            # 输出jenkins构建信息
            try:
                jenkins_job_build_result = jenkins.get_build_result(job_name, int(build_number))
                if str(jenkins_job_build_result) != "SUCCESS":
                    DsRedis.OpsProject.delete(redisKey=lock_id + "-locked")
                    return JsonResponse({'msg': "jenkins构建job失败", "code": 500, 'data': []})
                jenkins_job_output = jenkins.get_build_output(job_name, int(build_number))
                DsRedis.OpsDeploy.lpush(lock_id,
                                        data="Jenkins job info {info} ".format(info=jenkins_job_output))
                time.sleep(1)
            except Exception as ex:
                DsRedis.OpsProject.delete(redisKey=lock_id + "-locked")
                return JsonResponse({'msg': "jenkins构建job失败" + str(ex), "code": 500, 'data': []})
            if project.service.service_pom_path == "1":
                Project_Config.objects.filter(id=pid).update(project_status=1)
            else:
                services = Service_Assets.objects.filter(project_id=project.project_id, service_pom_path="0").values_list('id')
                Project_Config.objects.filter(service_id__in=services,project_env=project.project_env).update(project_status=1)
            DsRedis.OpsDeploy.lpush(lock_id,
                                    data="[Done] {name} compile Success.".format(name=project.service.service_name))
            DsRedis.OpsProject.delete(redisKey=lock_id + "-locked")
            recordProject(project_user=str(request.user), project_id=project.id,
                          project_name="编译打包", project_content="项目编译")
            return JsonResponse({'msg': "SUCCESS", "code": 200, 'data': []})
        else:
            return JsonResponse({'msg': "项目编译失败：{user}正在编译该项目，请稍后再提交编译。".format(
                user=DsRedis.OpsProject.get(redisKey=lock_id + "-locked")), "code": 500, 'data': []})
            # if project_group: return JsonResponse({'msg':project_group,"code":500,'data':[]})
        # else:
        #     Project_Config.objects.filter(id=pid).update(project_status = 1)
        #     recordProject(project_user=str(request.user),project_id=project.id,project_name=project.service.service_name,project_content="初始化项目")
        #     return JsonResponse({'msg':"初始化成功","code":200,'data':[]})

        
@login_required()
def deploy_run(request,pid):
    try:
        project = Project_Config.objects.get(id=pid)
        version = GitTools()
    except Exception as ex:
        logger.error(msg="项目部署失败: {ex}".format(ex=ex))
        return render(request,'deploy/deploy_run.html',{"user":request.user,
                                                         "errorInfo":"项目部署失败: {ex}".format(ex=ex)}, 
                                  )     
    if request.method == "GET":
        if project.project_env == 'prod':
            return render(request,'deploy/deploy_run.html',{"user":request.user,"project":project,
                                                             "errorInfo":"正式环境代码部署，请走工单审批流程"}, 
                                      )                    
        #获取最新版本
        vList = []
        vCommit = ""
        if project.project_env == "uat":
            version = GitTools()
            # vCommit = version.log(path=project.project_repo_dir, bName=project.project_branch, number=1)
            vTag = version.tag_number(path=project.project_repo_dir, bName=project.project_branch)
            deploy = Deploy_Record.objects.values('image_version').filter(run_env=project.project_env,
                                         service_name=project.service.service_name,
                                         project_name=project.project.project_name).order_by('-create_time')[0:1]
            # if vTag and deploy.count()>=1:
            #     for v in vTag:
            #         c=base.version_compare(v, deploy[0]['image_version'])
            #         if c: vList.append(c)
            #     if deploy[0]['image_version'] in vList: vList.remove(deploy[0]['image_version'])
            # else: vList=vTag
            # vList = list(set(vList))
            # if len(vList)>1: vList=list(set(vList))
        return render(request,'deploy/deploy_run.html',{"user":request.user,
                                                        "project":project,
                                                        "vList": vList,
                                                        "vCommit": vCommit})
        
    elif request.method == "POST":
        try:
            jenkins_client = JenkinsTools(
                host=project.jenkins.jenkins_host,
                username=project.jenkins.jenkins_user,
                password=project.jenkins.jenkins_token)
            k8s_client = K8sTools(
                api_host=str(project.k8s.k8s_host),
                token=str(project.k8s.k8s_token),
                namespace=str(project.project.project_english_name))
            if project.project_env == "uat" or project.project_env == "prod":
                project_version = request.POST.get('project_version')
            else:
                project_version = str(int(time.time()))
            if not project_version: return JsonResponse({'msg': 'Error: 上线版本号不能为空', "code": 500, 'data': []})
        except Exception as ex:
            logger.error(msg="项目部署失败: {ex}".format(ex=ex))
            return JsonResponse({'msg': str(ex), "code": 500, 'data': []})

        if DsRedis.OpsProject.get(redisKey=project.project_uuid+"-locked") is None:#判断该项目是否有人在部署
            #给项目部署加上锁
            DsRedis.OpsProject.set(redisKey=project.project_uuid+"-locked",value=request.user)
            DsRedis.OpsDeploy.delete(project.project_uuid)
            project_name = str(project.project.project_english_name)
            service_name = str(project.service.service_name)
            project_env = str(project.project_env)
            deployment_name = str(service_name + "-" + project_env)
            project_full_name = project_name + '-' + service_name + "-" + project_env
            build_type = str(project.service.service_type)
            mount_path = str(project.project_mount_path) if project.project_mount_path.strip() else None
            base_image = settings.DOCKER_IMAGE["jdk"] if build_type == "jar" else settings.DOCKER_IMAGE["tomcat"]
            registry = settings.DOCKER_REGISTRY["test"] if "test" in project_env else settings.DOCKER_REGISTRY["prod"]
            service_ip = settings.PROJECT_SERVICE_IP["test"] if "test" in project_env else settings.PROJECT_SERVICE_IP["prod"]
            image = str(registry + '/' + project_name + "-" + service_name + ":" + project_version)
            project_env_var = str(project.project_env_var.strip())

            if request.POST.get('project_model',None) == "rollback":
                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="项目开始回滚 ......")
                    k8s_client.create_deployment(name=deployment_name,
                                                 image=image,
                                                 env=project_env,
                                                 type=build_type,
                                                 rs=int(project.project_replication),
                                                 env_dict=project_env_var,
                                                 mount_path=mount_path)
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="项目：{name} info: 正在回滚......".format(name=project_name))
                    time.sleep(1)
                    active=2
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "项目回滚失败"+str(ex),"code":500,'data':[]})
            else:
                DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Application Initialization of project parameters ...... ]")
                #判断版本上线类型再切换分支到指定的分支/Tag
                if project_env_var:
                    try:
                        project_env_var=json.loads(project_env_var)
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg':"容器环境变量不是字典类型 " + str(ex),"code":500,'data':[]})
                else: project_env_var=None

                if project_env != 'prod' or project.project_category == "host" :

                    # 创建和更新jenkins job
                    try:
                        if project.project_category == "docker":
                            cmd = "cd {work_dir} &amp;&amp; jhhTool2 --project={project} --service={service} --env={env} --build_type={type} " \
                                    " --mode={mode} --base_image={base_image} --image={image}".format(work_dir=settings.PROJECT_WORK_DIR+"/"+project_name+"/"+service_name,
                                                                                              project=project_name,
                                                                                              service=service_name,
                                                                                              env=project_env,
                                                                                              type=project.service.service_type,
                                                                                              base_image=base_image,
                                                                                              image=image,
                                                                                              mode="docker")
                        else:
                            tagret_server = Project_Number.objects.filter(project=project.id).values_list('server')
                            serverObj = Server_Assets.objects.filter(ip__in=tagret_server)
                            serverList = []
                            sIndex=1
                            for s in serverObj:
                                serverList.append('{\\"hostname\\":\\"hn'+str(sIndex)+'\\",\\"ip\\":\\"'+s.ip+'\\",\\"username\\":\\"'+s.username+'\\",\\"password\\":\\"'+s.passwd+'\\"}')
                                sIndex+=1
                            cmd = " jhhTool2 --work_dir={work_dir} --project={project} --service={service} --env={env} --build_type={type} " \
                                   " --mode={mode} --server=&apos;{server}&apos; ".format(work_dir=settings.PROJECT_WORK_DIR+"/"+project_name+"/"+service_name,
                                                                              project=project_name,
                                                                              service=service_name,
                                                                              env=project_env,
                                                                              type=project.service.service_type,
                                                                              mode="host",
                                                                              server="@@@".join(serverList))
                        result=jenkins_client.create_deploy_job(str(project_full_name),str(cmd))
                        DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins start build jobs {job} info: {info}".format(job=project_full_name,info=result))
                        build_number = str(jenkins_client.get_next_build_number(project_full_name))
                        jenkins_client.build_job(project_full_name)
                        time.sleep(1)
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg': "jenkins创建job失败 " + str(ex), "code":500,'data':[]})

                    # 判断jenkins构建是否运行完毕
                    try:
                        building = True
                        DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins job building, wait a minute...... ")
                        while building:
                            build_status = jenkins_client.is_building(project_full_name, int(build_number))
                            if build_status: time.sleep(1)
                            else: building=False
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg': "jenkins构建job失败 " + str(ex), "code":500,'data':[]})

                    # 判断jenkins构建是否成功
                    try:
                        jenkins_job_build_result = jenkins_client.get_build_result(project_full_name, int(build_number))
                        if str(jenkins_job_build_result) != "SUCCESS":
                            DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                            return JsonResponse({'msg': "jenkins构建job失败", "code": 500, 'data': []})
                        jenkins_job_output = jenkins_client.get_build_output(project_full_name, int(build_number))
                        DsRedis.OpsDeploy.lpush(project.project_uuid,
                                                data="Jenkins job info {info} ".format(info=jenkins_job_output))
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg': "jenkins构建job错误 "+str(ex), "code":500,'data':[]})

                if project.project_category == "docker":
                    # 配置kubernetes相关参数
                    try:
                        k8s_client.create_namespace(project_name)
                        DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start k8s create namespace {namespace} info: {info}".format(namespace=project_name,info="命名空间更新成功"))
                        time.sleep(1)
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg':"kubernetes 创建命名空间失败" + str(ex),"code":500,'data':[]})

                    try:
                        k8s_client.create_deployment(name=deployment_name,
                                                     image=image,
                                                     env=project_env,
                                                     type=build_type,
                                                     rs=int(project.project_replication),
                                                     env_dict=project_env_var,
                                                     mount_path=mount_path)
                        DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start create deployment {name} info: {info}".format(name=deployment_name,info='POD创建成功'))
                        time.sleep(1)
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg': "kubernetes创建POD失败"+str(ex),"code":500,'data':[]})

                    try:
                        service_port = str(project.project_service_port) if project.project_service_port.strip() else None
                        debug_port = str(project.project_debug_port) if project.project_debug_port.strip() else None
                        result = k8s_client.create_service(deployment_name, service_port,debug_port)
                        DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start create service svc-{name} info: {info}".format(name=deployment_name,info=result))
                        active=1
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg':"kubernetes创建service失败"+str(ex),"code":500,'data':[]})

            DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Done] {name} Deploy Success.".format(name=project.service.service_name))
            #切换版本之后取消项目部署锁
            DsRedis.OpsProject.delete(redisKey=project.project_uuid+"-locked") 
            #异步记入操作日志

            recordProjectDeploy(user=str(request.user),project_name=project.project.project_name,
                                service_name=project.service.service_name,image_name=image,
                                run_env=str(project.project_env),is_online=active)
            Project_Config.objects.filter(id=project.id).update(project_status=0)
            recordProject(project_user=str(request.user), project_id=project.id,
                          project_name="项目发布", project_content="项目部署")
            # message_url_suffix = "/swagger-ui.html" if build_type == "jar" else service_name
            # xiaoding=chatbot.DingtalkChatbot(webhook=settings.DING_TALK)
            # xiaoding.send_link(
            #     title=project_name + ' 发布提醒',
            #     text='服务: ' + service_name + "\n环境：" + project_env + "\n端口：" + service_port,
            #     message_url="http://" + service_ip + ":" + service_port + message_url_suffix)            # message_url_suffix = "/swagger-ui.html" if build_type == "jar" else service_name
            # xiaoding=chatbot.DingtalkChatbot(webhook=settings.DING_TALK)
            # xiaoding.send_link(
            #     title=project_name + ' 发布提醒',
            #     text='服务: ' + service_name + "\n环境：" + project_env + "\n端口：" + service_port,
            #     message_url="http://" + service_ip + ":" + service_port + message_url_suffix)
            return JsonResponse({'msg':"项目部署成功","code":200,'data':project.project.project_name})
        else:
            return JsonResponse({'msg':"项目部署失败：{user}正在部署改项目，请稍后再提交部署。".format(user=DsRedis.OpsProject.get(redisKey=project.project_uuid+"-locked")),"code":500,'data':[]}) 


@login_required()
def deploy_result(request,pid):
    if request.method == "POST":
        msg = DsRedis.OpsDeploy.rpop(request.POST.get('project_uuid'))
        if msg:return JsonResponse({'msg':msg,"code":200,'data':[]}) 
        else:return JsonResponse({'msg': None,"code":200,'data':[]})

@login_required()
@permission_required('orders.can_add_project_order',login_url='/noperm/')
def deploy_order_status(request,pid):
    if request.method == "GET":
        try:
            order= Order_System.objects.get(id=pid)
            order.order_user = User.objects.get(id=order.order_user).username
            serverList = Project_Number.objects.filter(project=order.project_order.order_project)
            if order.order_user == str(request.user):order.order_perm = 'pass'
        except Exception as ex:
            logger.error(msg="获取代码部署工单失败: {ex}".format(ex=ex))
            return render(request,'orders/deploy_apply.html',{"user":request.user,
                                                "errorInfo":"获取代码部署工单失败: {ex}".format(ex=ex)}, 
                                              )             
        return render(request,'deploy/deploy_order_status.html',{"user":request.user,"order":order,"serverList":serverList},) 
    
    
@login_required()
@permission_required('orders.can_add_project_order',login_url='/noperm/')
def deploy_order_rollback(request,pid):
    try:
        project = Project_Config.objects.select_related().get(id=pid)
    except:
        return render(request, 'deploy/deploy_order_rollback.html', {"user": request.user,
                                                              "errorInfo": "项目不存在，可能已经被删除."})

    if request.method == "GET" and project.project_env in ('prod', 'uat'):
        vList = Deploy_Record.objects.values('image_version').filter(run_env=project.project_env,
                                                                      service_name=project.service.service_name,
                                                                      project_name=project.project.project_name).order_by('-create_time')[1:5]
        return render(request,'deploy/deploy_order_rollback.html', {"user":request.user,"project":project,"vList":vList})
    else:
        return render(request, 'deploy/deploy_order_rollback.html', {"user": request.user,
                                                              "errorInfo": "项目不存在，可能已经被删除."})


@login_required()
def deploy_manage(request,pid):
    try:
        project = Project_Config.objects.get(id=pid)
        version = GitTools()
    except:
        return render(request,'deploy/deploy_manage.html',{"user":request.user,
                                                         "errorInfo":"项目不存在，可能已经被删除."}, 
                                  ) 
    if request.method == "GET":
        #获取最新版本
        version.pull(path=project.project_repo_dir)
        bList = version.branch(path=project.project_repo_dir)
        vList = version.log(path=project.project_repo_dir, number=50)
        return render(request,'deploy/deploy_manage.html',{"user":request.user,
                                                         "project":project,
                                                         "bList":bList,"vList":vList}, 
                                  )


@login_required(login_url='/login')  
def deploy_log(request,page):
    if request.method == "GET":
        allProjectList = Log_Project_Config.objects.all().order_by('-id')[0:1000]
        for ds in allProjectList:
            try:
                ds.project = Project_Config.objects.get(id=ds.project_id)
            except Exception as ex:
                logger.info(msg="项目id: {ex}可能已经被删除了".format(ex=ex))
        paginator = Paginator(allProjectList, 25)
        try:
            projectList = paginator.page(page)
        except PageNotAnInteger:
            projectList = paginator.page(1)
        except EmptyPage:
            projectList = paginator.page(paginator.num_pages)        
        return render(request,'deploy/deploy_log.html',{"user":request.user,"projectList":projectList},
                                  )


@login_required(login_url='/login')
def deploy_record(request,page):
    if request.method == "GET":
        pageNum=10      # 每页行数
        displayPageNum=5   # 显示页数
        allProjectList = Deploy_Record.objects.all().order_by('-id')
        paginator = Paginator(allProjectList, pageNum)
        try:
            projectList = paginator.page(page)
        except PageNotAnInteger:
            projectList = paginator.page(1)
        except EmptyPage:
            projectList = paginator.page(paginator.num_pages)
        try:
            page = int(page)
            if page <= 1: page_range = range(1, displayPageNum + 1)
            elif paginator.num_pages <= displayPageNum:
                page_range = range(1, paginator.num_pages)
            elif paginator.num_pages-page <= displayPageNum:
                page_range = range(paginator.num_pages - displayPageNum, paginator.num_pages+1)
            else: page_range = range(page, page+displayPageNum)
        except:
            page_range = range(1, displayPageNum+1)
        return render(request,'deploy/deploy_record.html',{"user":request.user,"projectList":projectList,"page_range":page_range},
                                  )