#!/usr/bin/env python
# _#_ coding:utf-8 _*_

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.credential import UsernamePasswordCredential
import jenkins


class JenkinsTools(object):

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    @property
    def jenkinsConn(self):
        return Jenkins(self.host, self.username, self.password)

    @property
    def jkConn(self):
        return jenkins.Jenkins(url=self.host, username=self.username, password=self.password)

    def create_credential(self, username, password, c_id):
        if self._has_credentials(c_id): self.del_credentials(c_id)
        creds = self.jenkinsConn.credentials
        cred_dict = {
            'description': c_id,
            'userName': username,
            'password': password,
            'credential_id': c_id
        }
        creds[c_id] = UsernamePasswordCredential(cred_dict)
        return creds[c_id]

    def get_credentials(self):
        return self.jenkinsConn.credentials.keys()

    def del_credentials(self, name):
        try:
            if self._has_credentials(name):
                del self.jenkinsConn.credentials[name]
            return True
        except Exception as ex:
            return False

    def _has_credentials(self, name):
        return True if name in self.get_credentials() else False

    def create_job(self, name, git_brach, git_user, git_url, shell_cmd):
        compile_cmd = "mvn clean install -Dmaven.test.skip=true"
        config = '''
            <flow-definition plugin="workflow-job@2.21">
                <actions>
                    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobAction plugin="pipeline-model-definition@1.2.9"/>
                    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction plugin="pipeline-model-definition@1.2.9">
                    <jobProperties/>
                    <triggers/>
                    <parameters/>
                    </org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction>
                </actions>
                <description></description>
                <keepDependencies>false</keepDependencies>
                <properties>
                    <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.5.5">
                        <gitLabConnection></gitLabConnection>
                    </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>
                </properties>
                <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.53">
                <script>pipeline {
                  agent {
                    label &apos;master&apos;
                  }
                  stages {
                    stage(&apos;git pull&apos;) {
                      steps {
                        git branch: &apos;%s&apos;, credentialsId: &apos;%s&apos;, url: &quot;%s&quot;
                      }
                    }
                  stage(&apos;start docker&apos;) {
                      steps {
                        sh &quot;%s&quot;
                        sh &quot;%s&quot;
                      }
                    }
                  }
              }</script>
              <sandbox>true</sandbox>
              </definition>
              <triggers/>
              <disabled>false</disabled>
            </flow-definition>
            ''' % (git_brach, git_user, git_url, compile_cmd, shell_cmd)
        return self.jkConn.reconfig_job(name, config) if self.jkConn.job_exists(name) else self.jkConn.create_job(name, config)

    def create_deploy_job(self, job_name, cmd):
        config = '''
            <flow-definition plugin="workflow-job@2.21">
                <actions>
                    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobAction plugin="pipeline-model-definition@1.2.9"/>
                    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction plugin="pipeline-model-definition@1.2.9">
                    <jobProperties/>
                    <triggers/>
                    <parameters/>
                    </org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction>
                </actions>
                <description></description>
                <keepDependencies>false</keepDependencies>
                <properties>
                    <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.5.5">
                        <gitLabConnection></gitLabConnection>
                    </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>
                </properties>
                <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.53">
                <script>pipeline {
                  agent {
                    label &apos;master&apos;
                  }
                  stages {
                    stage(&apos;start deploy&apos;) {
                      steps {
                        sh &quot;%s&quot;
                      }
                    }
                  }
              }</script>
              <sandbox>true</sandbox>
              </definition>
              <triggers/>
              <disabled>false</disabled>
            </flow-definition>
            ''' % (cmd)
        return self.jkConn.reconfig_job(job_name, config) if self.jkConn.job_exists(job_name) else self.jkConn.create_job(job_name, config)

    def has_job(self, name):
        return self.jkConn.job_exists(name)

    def has_node(self, name):
        return self.jkConn.node_exists(name)

    def build_job(self, name):
        return self.jkConn.build_job(name) if self.has_job(name) else False

    def get_next_build_number(self, name):
        return str(self.jkConn.get_job_info(name)['nextBuildNumber'])

    def get_build_result(self, name, number):
        return self.jkConn.get_build_info(name, number)['result']

    def is_building(self, name, number):
        return self.jkConn.get_build_info(name, number)['building']

    def get_build_output(self, name, number):
        return self.jkConn.get_build_console_output(name, number)

    def get_config(self,name):
        return self.jkConn.get_job_config(name)
