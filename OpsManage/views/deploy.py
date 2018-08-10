#!/usr/bin/env python  
# _*_ coding:utf-8 _*_
import uuid,os
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from OpsManage.models import (Project_Assets,Server_Assets,Project_Config,
                                Project_Number,Log_Project_Config,Service_Assets,Assets,
                              Jenkins_Assets,K8s_Assets, Deploy_Record)
from OpsManage.utils.git import GitTools
from OpsManage.utils.svn import SvnTools
from OpsManage.utils import base
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
from dao.assets import AssetsSource
import json
import time

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
        try:
            proAssets = Project_Assets.objects.get(id=request.POST.get('project_id'))
            jenAssets = Jenkins_Assets.objects.get(id=request.POST.get('jenkins_id'))
            k8sAssets = K8s_Assets.objects.get(id=request.POST.get('k8s_id'))
            svcAssets = Service_Assets.objects.get(id=request.POST.get('service_id'))
        except Exception as ex:
            return JsonResponse({'msg':"部署项目添加失败".format(ex=ex),"code":500,'data':[]})     
        try: 
            project = Project_Config.objects.create(
                                                    project = proAssets,
                                                    project_env = request.POST.get('project_env'),
                                                    project_local_command = request.POST.get('project_local_command'),
                                                    project_dir = request.POST.get('project_dir'),
                                                    project_uuid = uuid.uuid4(),
                                                    project_status = 0,
                                                    project_repo_dir=request.POST.get('project_repo_dir'),
                                                    project_address=request.POST.get('project_address'),
                                                    project_repo_user = request.POST.get('project_repo_user'),
                                                    project_repo_passwd = request.POST.get('project_repo_passwd'),
                                                    project_branch = request.POST.get('project_branch'),
                                                    project_type=request.POST.get('project_type'),
                                                    project_repertory = request.POST.get('project_repertory'),
                                                    jenkins= jenAssets,
                                                    k8s = k8sAssets,
                                                    service = svcAssets,
                                                    project_service_port = request.POST.get('project_service_port'),
                                                    project_debug_port = request.POST.get('project_debug_port'),
                                                    project_env_var = request.POST.get('project_env_var'),
                                                    project_mount_path = request.POST.get('project_mount_path')
                                                    )
            recordProject(project_user=str(request.user),project_id=proAssets.id,project_name=proAssets.project_name,project_content="添加代码发布项目")
        except Exception as ex:
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
    except Exception as ex:
        logger.error(msg="修改项目失败: {ex}".format(ex=ex))
        return render(request,'deploy/deploy_modf.html',{"user":request.user,
                                                         "errorInfo":"修改项目失败: {ex}".format(ex=ex)},
                                )  
    if request.method == "GET":
        serviceList = Service_Assets.objects.filter(project=project.project)
        groupList = Group.objects.all()
        return render(request,'deploy/deploy_modf.html',{"user":request.user,"project":project,"k8s":k8s,
                                                         "jenkins":jenkins,"groupList":groupList,"serviceList":serviceList},)
    elif request.method == "POST":
        try:      
            Project_Config.objects.filter(id=pid).update(
                                                    project_env = request.POST.get('project_env'),  
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
                                                    jenkins_id=request.POST.get('jenkins_id'),
                                                    k8s_id=request.POST.get('k8s_id'),
                                                    project_service_port=request.POST.get('project_service_port'),
                                                    project_debug_port=request.POST.get('project_debug_port'),
                                                    project_env_var=request.POST.get('project_env_var'),
                                                    project_mount_path=request.POST.get('project_mount_path')
                                                    )
            recordProject(project_user=str(request.user),project_id=pid,project_name=project.project_name,project_content="修改项目")
        except Exception as ex:
            logger.error(msg="部署项目修改失败: {ex}".format(ex=ex))
            return JsonResponse({'msg':"部署项目修改失败: {ex}".format(ex=ex),"code":500,'data':[]})
    return JsonResponse({'msg':"部署项目修改成功","code":200,'data':[]})         
        
@login_required()
@permission_required('OpsManage.can_read_project_config',login_url='/noperm/')
def deploy_list(request):
    deployList = Project_Config.objects.all()
    for ds in deployList:
        ds.number = Project_Number.objects.filter(project=ds)
    uatProject = Project_Config.objects.filter(project_env="uat").count()
    testProject = Project_Config.objects.filter(project_env="test").count()
    prodProject = Project_Config.objects.filter(project_env="prod").count()
    return render(request,'deploy/deploy_list.html',{"user":request.user,"totalProject":deployList.count(),
                                                         "deployList":deployList,"uatProject":uatProject,
                                                         "testProject":testProject,"prodProject":prodProject},
                              )  
    
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
def deploy_run(request,pid): 
    try:
        project = Project_Config.objects.get(id=pid)
        if project.project_repertory == 'git':version = GitTools()
        elif project.project_repertory == 'svn':version = SvnTools()
    except Exception as ex:
        logger.error(msg="项目部署失败: {ex}".format(ex=ex))
        return render(request,'deploy/deploy_run.html',{"user":request.user,
                                                         "errorInfo":"项目部署失败: {ex}".format(ex=ex)}, 
                                  )     
    if request.method == "GET":
        if project.project_env == 'prod':
            return render(request,'deploy/deploy_run.html',{"user":request.user,
                                                             "project":project,
                                                             "errorInfo":"正式环境代码部署，请走工单审批流程"}, 
                                      )                    
        #获取最新版本
        return render(request,'deploy/deploy_run.html',{"user":request.user,
                                                        "project":project
                                                        }
                                  ) 
        
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
        except Exception as ex:
            logger.error(msg="项目部署失败: {ex}".format(ex=ex))
            return JsonResponse({'msg': str(ex), "code": 500, 'data': []})

        if DsRedis.OpsProject.get(redisKey=project.project_uuid+"-locked") is None:#判断该项目是否有人在部署
            #给项目部署加上锁

            DsRedis.OpsProject.set(redisKey=project.project_uuid+"-locked",value=request.user)
            DsRedis.OpsDeploy.delete(project.project_uuid)  
            if request.POST.get('project_model',None) == "rollback":
                project_content = "回滚项目"
                if project.project_model == 'branch':
                    verName = request.POST.get('project_version') 
                    trueDir = project.project_dir+project.project_env+'/'+ request.POST.get('project_version')  + '/'
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="[PULL] Start Rollback branch:%s  vesion: %s" % (request.POST.get('project_branch'),request.POST.get('project_version')))
                elif  project.project_model == 'tag':
                    verName = request.POST.get('project_branch') 
                    trueDir = project.project_dir+project.project_env+'/'+ request.POST.get('project_branch') + '/'
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="[PULL] Start Rollback tag:%s" % request.POST.get('project_branch'))
                #创建版本目录
                base.mkdir(dirPath=trueDir)
                DsRedis.OpsDeploy.lpush(project.project_uuid, data="[PULL] Mkdir version dir: {dir} ".format(dir=trueDir))
                #创建快捷方式
                softdir = project.project_dir+project.project_name+'/'
                result = base.lns(spath=trueDir, dpath=softdir.rstrip('/'))
                DsRedis.OpsDeploy.lpush(project.project_uuid, data="[PULL] Make softlink cmd:  ln -s  {sdir} {ddir} info: {info}".format(sdir=trueDir,ddir=softdir,info=result[1]))
                if result[0] > 0:return JsonResponse({'msg':result[1],"code":500,'data':[]})    
                #获取要排除的文件 
                exclude = None
                if project.project_exclude:
                    try:
                        exclude = ''
                        for s in project.project_exclude.split(','):
                            exclude = "--exclude='{file}'".format(file=s.replace('\r\n','').replace('\n','').strip()) + ' ' + exclude
                    except Exception as e:
                        return JsonResponse({'msg':str(e),"code":500,'data':[]})                                 
            else:
                DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Application Initialization of project parameters ...... ]")
                #判断版本上线类型再切换分支到指定的分支/Tag

                project_name = str(project.project.project_english_name.strip())
                service_name = str(project.service.service_name.strip())
                project_env = str(project.project_env)
                deployment_name = str(service_name + "-" + project_env)
                project_full_name = project_name + '-' + service_name + "-" + project_env
                repo_user = project.project_repo_user
                repo_passwd = project.project_repo_passwd
                repo_branch = project.project_branch
                repo_host = project.project_address
                build_type = str(project.service.service_type)
                mount_path = str(project.project_mount_path) if project.project_mount_path.strip() else None
                base_image = settings.DOCKER_IMAGE["jdk"] if build_type == "jar" else settings.DOCKER_IMAGE["tomcat"]
                registry = settings.DOCKER_REGISTRY["test"] if project_env == "test" else settings.DOCKER_REGISTRY["prod"]
                service_ip = settings.PROJECT_SERVICE_IP["test"] if project_env == "test" else settings.PROJECT_SERVICE_IP["prod"]
                image = str(registry+'/'+project_name+"-"+service_name + ":" + str(int(time.time())))
                project_env_var=str(project.project_env_var.strip())

                if project_env_var:
                    try:
                        project_env_var=json.loads(project_env_var)
                    except Exception as ex:
                        DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                        return JsonResponse({'msg':"容器环境变量不是字典类型 " + str(ex),"code":500,'data':[]})
                else:
                    project_env_var=None

                try:
                    jenkins_client.create_credential(
                        username=str(repo_user),
                        password=str(repo_passwd),
                        c_id=str(project_full_name))
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Jenkins start create credential %s" % project_full_name)
                    time.sleep(1)
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins create Credentials fail " + str(ex), "code": 500, 'data': []})

                # 创建和更新jenkins job
                try:
                    cmd = "jhhTool --project={project} --service={service} --env={env} --k8s={k8s}" \
                          " --ding={ding} --type={type} --user={user} --url={url} --baseImage={base_image} " \
                          " --image={image} --registry={registry}".format(project=project_name,
                                                                          service=service_name,
                                                                          env=project_env,
                                                                          k8s="False",
                                                                          ding="False",
                                                                          type=project.service.service_type,
                                                                          user=request.user,
                                                                          url="False",
                                                                          base_image=base_image,
                                                                          image=image,
                                                                          registry=registry)
                    result=jenkins_client.create_job(str(project_full_name),
                                                     str(repo_branch),
                                                     str(project_full_name),
                                                     str(repo_host),
                                                     str(cmd))
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins start create jobs {job} info: {info}".format(job=project_full_name,info=result))
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins创建job失败" + str(ex), "code":500,'data':[]})

                # 获取jenkins的下一次构建number号
                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins get build job next number...... ")
                    build_number=str(jenkins_client.get_next_build_number(project_full_name))
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins build job {name} info: job number{info}".format(name=project_full_name, info=str(build_number)))
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins获取项目构建number失败" + str(ex), "code":500,'data':[]})

                # 触发jenkins构建
                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins start build job ...... ")
                    result = jenkins_client.build_job(project_full_name)
                    DsRedis.OpsDeploy.lpush(project.project_uuid,data="Jenkins start build job {name} info: {info}".format(name=project_full_name, info=result))
                    time.sleep(2)
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins触发job构建失败" + str(ex), "code":500,'data':[]})

                # 判断jenkins构建是否运行完毕
                try:
                    building = True
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Jenkins job {name} building, wait a minute...... ".format(name=project_full_name))
                    while building:
                        build_status = jenkins_client.is_building(project_full_name, int(build_number))
                        if build_status:
                            time.sleep(2)
                        else:
                            building=False
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins获取构建状态失败" + str(ex), "code":500,'data':[]})

                # 判断jenkins构建是否成功
                try:
                    jenkins_job_build_result = jenkins_client.get_build_result(project_full_name, int(build_number))
                    if jenkins_job_build_result != "SUCCESS":
                        return JsonResponse({'msg': "jenkins构建job失败", "code": 500, 'data': []})
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins构建job失败" + str(ex), "code":500,'data':[]})

                # 输出jenkins构建信息
                try:
                    jenkins_job_output = jenkins_client.get_build_output(project_full_name, int(build_number))
                    DsRedis.OpsDeploy.lpush(project.project_uuid,data="Jenkins job info {info} ".format(info=jenkins_job_output))
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "jenkins构建job信息输出失败" + str(ex), "code":500,'data':[]})

                # 配置kubernetes相关参数
                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Kubernetes start create namespace ...... ]")
                    result = k8s_client.create_namespace(project_name)
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start k8s create namespace {namespace} info: {info}".format(namespace=project_name,info=result))
                    time.sleep(1)
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg':"kubernetes 创建命名空间失败" + str(ex),"code":500,'data':[]})

                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start create deployment ......")
                    k8s_client.create_deployment(name=deployment_name,
                                                 image=image,
                                                 env=project_env,
                                                 type=build_type,
                                                 env_dict=project_env_var,
                                                 mount_path=mount_path)
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start create deployment {name} info: {info}".format(name=deployment_name,info='POD创建成功'))
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg': "kubernetes创建POD失败"+str(ex),"code":500,'data':[]})

                try:
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Kubernetes start create service ...... ]")
                    service_port = str(project.project_service_port) if project.project_service_port.strip() else None
                    debug_port = str(project.project_debug_port) if project.project_debug_port.strip() else None
                    result = k8s_client.create_service(deployment_name, service_port,debug_port)
                    DsRedis.OpsDeploy.lpush(project.project_uuid, data="Kubernetes start create service svc-{name} info: {info}".format(name=deployment_name,info=result))
                except Exception as ex:
                    DsRedis.OpsProject.delete(redisKey=project.project_uuid + "-locked")
                    return JsonResponse({'msg':"kubernetes创建service失败"+str(ex),"code":500,'data':[]})

            DsRedis.OpsDeploy.lpush(project.project_uuid, data="[Done] {name} Deploy Success.".format(name=project.service.service_name))
            #切换版本之后取消项目部署锁
            DsRedis.OpsProject.delete(redisKey=project.project_uuid+"-locked") 
            #异步记入操作日志

            recordProjectDeploy(user=str(request.user),project_name=project.project.project_name,
                                service_name=project.service.service_name,image_name=image,
                                run_env=str(project.project_env),is_online=1)
            return JsonResponse({'msg':"项目部署成功","code":200,'data':project.project.project_name})
        else:
            return JsonResponse({'msg':"项目部署失败：{user}正在部署改项目，请稍后再提交部署。".format(user=DsRedis.OpsProject.get(redisKey=project.project_uuid+"-locked")),"code":500,'data':[]}) 
                        
@login_required()
def deploy_result(request,pid):
    if request.method == "POST":
        msg = DsRedis.OpsDeploy.rpop(request.POST.get('project_uuid'))
        if msg:return JsonResponse({'msg':msg,"code":200,'data':[]}) 
        else:return JsonResponse({'msg':None,"code":200,'data':[]})
        
        
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
    if request.method == "GET":
        order= Order_System.objects.get(id=pid)
        order.order_user = User.objects.get(id=order.order_user).username
        return render(request,'deploy/deploy_order_rollback.html',{"user":request.user,"order":order},) 
    
    
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
        allProjectList = Deploy_Record.objects.all().order_by('-id')[0:1000]
        paginator = Paginator(allProjectList, 1000)
        try:
            projectList = paginator.page(page)
        except PageNotAnInteger:
            projectList = paginator.page(1)
        except EmptyPage:
            projectList = paginator.page(paginator.num_pages)
        return render(request,'deploy/deploy_record.html',{"user":request.user,"projectList":projectList},
                                  )