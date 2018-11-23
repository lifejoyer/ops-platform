#!/usr/bin/env python  
# _#_ coding:utf-8 _*_ 
'''git版本控制方法'''

import os
import subprocess
from OpsManage.utils import base


class GitTools(object):
       
    def reset(self,path,commintId):
        cmd = "cd {path} && git reset --hard {commintId}".format(path=path,commintId=commintId)
        return subprocess.getstatusoutput(cmd)
    
    def log(self,path,bName=None,number=None):
        vList = []
        if bName:cmd = "cd {path} && git log {bName} --pretty=format:'%h|%s|%cn|%ci|%H' -n {number}".format(path=path,bName=bName,number=number)
        else:cmd = "cd {path} && git log --pretty=format:'%h|%s|%cn|%ci|%H' -n {number}".format(path=path,number=number)
        status,result = subprocess.getstatusoutput(cmd)
        if status == 0: 
            for log in result.split('\n'):
                log = log.split('|')
                data = dict()
                data['ver'] = log[0]
                data['desc'] = log[1]
                data['user'] = log[2]
                data['comid'] = log[4]
                vList.append(data)
        return vList    
    
    def init(self,path): 
        cmd = "cd {path} && git init".format(path=path)
        return subprocess.getstatusoutput(cmd)
    
    def branch(self,path):
        '''获取分支列表'''
        bList = []
        cmd = "cd {path} && git branch".format(path=path)
        status,result = subprocess.getstatusoutput(cmd)
        if status == 0: 
            for ds in result.split('\n'):
                if len(ds) == 0:continue
                data = dict()
                if ds.find('*') >= 0:data['status'] = 1
                else:data['status'] = 0
                data['name'] = ds.replace('* ','').strip() 
                data['value'] =  ds.replace('* ','').strip()
                bList.append(data)        
        return  bList      
        
    def createBranch(self,path,branchName):
        cmd = "cd {path} && git checkout -b {branchName} origin/{branchName}".format(path=path,branchName=branchName)
        return subprocess.getstatusoutput(cmd)
    
    def delBranch(self,path,branchName):
        cmd = "cd {path} && git branch -d {branchName}".format(path=path,branchName=branchName)
        return subprocess.getstatusoutput(cmd)

    def tag(self,path):
        tagList = []
        cmd = "cd {path} && git tag".format(path=path)
        status,result = subprocess.getstatusoutput(cmd)
        if status == 0: 
            for ds in result.split('\n'):
                if len(ds) == 0:continue
                data = dict()
                if ds.find('*') >= 0:data['status'] = 1
                else:data['status'] = 0                
                data['name'] = ds.replace('* ','').strip() 
                data['value'] = ds.strip()
                tagList.append(data)         
        return  tagList
    
    def createTag(self,path,tagName):
        cmd = "cd {path} && git tag {tagName}".format(path=path,tagName=tagName)
        return subprocess.getstatusoutput(cmd)
    
    def delTag(self,path,tagName):
        cmd = "cd {path} && git tag -d {tagName}".format(path=path,tagName=tagName)
        return subprocess.getstatusoutput(cmd)
     
    def checkOut(self,path,name):
        cmd = "cd {path} && git checkout {name}".format(path=path,name=name)
        return subprocess.getstatusoutput(cmd)
    
    def clone(self,url, dir, user=None, passwd=None):
        if user and passwd:
            git_url = str(url).split("://")[-1]
            url = "http://" + user + ":" + passwd + "@" + git_url
        cmd_init = "git config --global credential.helper store"
        cmd_clone = "git clone {url} {dir}".format(url=url, dir=dir)
        subprocess.getstatusoutput(cmd_init)
        return subprocess.getstatusoutput(cmd_clone)
        
    def pull(self,path):     
        cmd = "cd {path} && git pull".format(path=path)           
        return subprocess.getstatusoutput(cmd)
            
    def mkdir(self,dir):
        if not os.path.exists(dir): os.makedirs(dir)
          
    def show(self,path,branch,cid):
        cmd = "cd {path} && git checkout {branch}".format(path=path,branch=branch) 
        result = subprocess.getstatusoutput(cmd)
        if result[0] == 0 and cid: 
            cmd = "cd {path} &&  git show {cid}".format(path=path,cid=cid)    
            result = subprocess.getstatusoutput(cmd)
        return result

    def tag_number(self, path, bName):
        try:
            tagList=[]
            res = subprocess.check_output("cd {path} && git checkout {branch} && git pull && git tag|head -n 5".format(path=path,branch=bName), stderr=subprocess.STDOUT, shell=True)
            res = res.splitlines()
            for i in range(0, len(res)):
                if base.is_version(res[i].decode()): tagList.append(res[i].decode())
            return tagList
        except Exception as e:
            return False
