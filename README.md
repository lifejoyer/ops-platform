## ops-platform的作用？
一款代码部署、计划任务、主机管理平台。

## 开发语言与框架：
 * 编程语言：Python2.7.5 + HTML + JScripts
 * 前端Web框架：Bootstrap
 * 后端Web框架：Django

## ops-platform环境要求
 * 编程语言：Python 2.7.5
 * 操作系统：CentOS 6.5+
 * Ansible版本：2.0 + 
 * MySQL版本：5.6+

## 安装环境配置
一、安装Python
```
# yum install zlib zlib-devel readline-devel sqlite-devel bzip2-devel openssl-devel gdbm-devel libdbi-devel ncurses-libs kernel-devel libxslt-devel libffi-devel python-devel mysql-devel zlib-devel mysql-server sshpass gcc git -y
# wget http://mirrors.sohu.com/python/2.7.12/Python-2.7.12.tgz  #CentOS 7不用安装python2.7,默认自带2.7.5
# tar -xzvf Python-2.7.12.tgz
# cd Python-2.7.12
# ./configure
# make all
# make install
# make clean
# make distclean 
# mv /usr/bin/python /usr/bin/python2.6.6  
# ln -s /usr/local/bin/python2.7 /usr/bin/python 
# vi /usr/bin/yum  
将文件头部的
#!/usr/bin/python

改成
#!/usr/bin/python2.6.6
```
二、安装easy_install
```
# wget --no-check-certificate  https://pypi.python.org/packages/f7/94/eee867605a99ac113c4108534ad7c292ed48bf1d06dfe7b63daa51e49987/setuptools-28.0.0.tar.gz#md5=9b23df90e1510c7353a5cf07873dcd22
# tar -xzvf setuptools-28.0.0.tar.gz
# cd setuptools-28.0.0
# python  setup.py  install
```

三、安装pip
```
# wget --no-check-certificate https://github.com/pypa/pip/archive/1.5.5.tar.gz -O pip-1.5.5.tar.gz
# tar -xzvf pip-1.5.5.tar.gz
# cd pip-1.5.5/
# python setup.py install
# pip install -U pip 
```

四、安装模块
```
# cd /mnt/
# git clone https://github.com/welliamcao/OpsManage.git
# cd /mnt/OpsManage/
# pip install -r requirements.txt  #注意，如果出现错误不要跳过，请根据错误信息尝试解决
# easy_install paramiko==2.4.1
```

五、安装Redis
```
# wget http://download.redis.io/releases/redis-3.2.8.tar.gz
# tar -xzvf redis-3.2.8.tar.gz
# cd redis-3.2.8
# make
# make install
# vim redis.conf
```
修改以下配置
```
daemonize yes
loglevel warning
logfile "/var/log/redis.log"
bind 你的服务器ip地址
例如： bind 127.0.0.1 192.168.88.201
```
```
# cd ../
# mv redis-3.2.8 /usr/local/redis
# /usr/local/redis/src/redis-server /usr/local/redis/redis.conf
```
六、配置MySQL
```
# vim /etc/my.cnf
[mysqld]
character_set_server = utf8
添加以上字段
```
```
# mysql -uroot -p
mysql> create database opsmanage DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
mysql> grant all privileges on opsmanage.* to root@'%' identified by 'password';
mysql>\q
# /etc/init.d/mysqld restart
```
七、配置OpsManage
```
# cd /opt/ops-platform/OpsManage
# vim settings.py
BROKER_URL =  redis://192.168.1.233:6379/3 #修改成自己的配置，格式是redis://[:password]@host:port/db
REDSI_KWARGS_LPUSH = {"host":'192.168.1.233','port':6379,'db':3} #修改成自己的配置
DATABASES = {
    'default': {
        'ENGINE':'django.db.backends.mysql',
        'NAME':'ops-platform',
        'USER':'root',		#修改成自己的配置
        'PASSWORD':'welliam',	#修改成自己的配置
        'HOST':'192.168.1.233', #修改成自己的配置
        'PORT': 3306
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["/opt/ops-platform/OpsManage/static/",'/opt/ops-platform/OpsManage/templates/'], #修改成自己的配置
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
STATICFILES_DIRS = (
     '/opt/ops-platform/OpsManage/static/',	#修改成自己的配置
    )
TEMPLATE_DIRS = (
#     os.path.join(BASE_DIR,'mysite\templates'),
    '/opt/ops-platform/OpsManage/templates/',	#修改成自己的配置
)

```
八、生成数据表与管理员账户
```
# cd /opt/ops-platform/
# python manage.py makemigrations OpsManage
# python manage.py makemigrations wiki
# python manage.py makemigrations orders
# python manage.py makemigrations filemanage
# python manage.py migrate
# python manage.py createsuperuser
```
九、启动部署平台
```
# cd /opt/ops-platform/
# python manage.py runserver 0.0.0.0:8000
```
十、配置证书认证
```
# ssh-keygen -t  rsa
# ssh-copy-id -i ~/.ssh/id_rsa.pub  root@ipaddress
```
