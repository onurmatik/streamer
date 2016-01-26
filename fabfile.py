"""
sudo aptitude update
sudo aptitude -y install libxml2-dev libxslt1-dev python-dev python-libxml2 python-setuptools libpq-dev build-essential
sudo aptitude -y install libpq-dev git-core build-essential nginx-full python-psycopg2 python-virtualenv
"""




# for AMI ami-ab9491df (Ubuntu 12 LTS)


import os
from fabric.contrib import files
from fabric.decorators import task
from fabric.operations import run, prompt
from fabric.api import env, local, sudo, put


env.domain = "stream.do"

env.hosts = ["ec2-52-28-57-224.eu-central-1.compute.amazonaws.com"]

env.user = "ubuntu"
env.key_filename = "~/.ssh/aws-frankfurt.pem"

env.nginx_hosts = ' '.join(env.hosts + [env.domain])

env.git_repo = local('git config --get remote.origin.url', capture=True)
env.project_name = env.git_repo.split('/')[-1].split('.')[0]  # use git file name

env.project_dir = os.path.realpath(os.path.join(os.path.dirname(env.real_fabfile), ".."))
env.server_project_base = '/home/%s' % env.user
env.server_project_dir = os.path.join(env.server_project_base, env.project_name)
env.environment_dir = '%s/env/' % env.server_project_dir
env.warn_only = True

PACKAGES = (
    "libxml2-dev libxslt1-dev python-dev python-libxml2 python-setuptools git-core build-essential libpq-dev",
    "nginx-full",
    "python-psycopg2",
    "python-virtualenv",
)


@task
def copy_keys():
    run("mkdir -p ~/.ssh/")
    put("~/.ssh/id_rsa", "~/.ssh/id_rsa", mode=0600)
    put("~/.ssh/id_rsa.pub", "~/.ssh/id_rsa.pub", mode=0600)
    put("~/.ssh/known_hosts", "~/.ssh/known_hosts", mode=0600)


@task
def setup():
    # install packages
    sudo("aptitude update")
    sudo("aptitude -y install %s" % (' '.join(PACKAGES),))

    # git basic configuration
    sudo("git config --global user.name 'onurmatik'; git config --global user.email 'omat@teknolab.org';")

    # clone repo
    copy_keys()
    run("cd %(server_project_base)s; git clone %(git_repo)s;" % env)

    sudo("pip install uwsgi")

    # use --system-site-packages; psycopg2 is installed globally
    run("virtualenv --system-site-packages %s" % env.environment_dir)
    run('''source %(environment_dir)sbin/activate;
           pip install -r %(server_project_dir)s/requirements.txt''' % env)

    # nginx
    files.upload_template("%(project_dir)s/deploy/nginx/server.conf" % env,
                          "/etc/nginx/nginx.conf", use_sudo=True, context=env)
    files.upload_template("%(project_dir)s/deploy/nginx/site.conf" % env,
                          "/etc/nginx/sites-available/default.conf",
                          context=env, use_sudo=True)

    # uwsgi
    files.put("%s/deploy/uwsgi/upstart.conf" % env.project_dir,
              "/etc/init/uwsgi.conf", use_sudo=True)

    sudo("rm -f /etc/uwsgi/apps-available/%(project_name)s.ini" % env)
    sudo("rm -f /etc/uwsgi/apps-enabled/%(project_name)s.ini" % env)
    files.upload_template("%(project_dir)s/deploy/uwsgi/app.ini" % env,
                          "/etc/uwsgi/apps-available/%(project_name)s.ini" % env,
                          use_sudo=True, context=env)
    sudo('''ln -s /etc/uwsgi/apps-available/%(project_name)s.ini \
            /etc/uwsgi/apps-enabled/%(project_name)s.ini''' % env)

    deploy()


@task
def deploy():
    run("cd %(server_project_dir)s/;"
        "git pull origin master;"
        "pip install -r %(server_project_dir)s/requirements.txt;"
        "python manage.py migrate;"
        "python manage.py collectstatic --noinput;" % env)
    restart()


@task
def restart():
    sudo("service uwsgi stop; service uwsgi start", pty=False)
    sudo("service nginx stop; service nginx start", pty=False)
    sudo("/etc/init.d/celeryd restart", pty=False)
    sudo("/etc/init.d/celerybeat restart", pty=False)


@task
def git_optimize():
    run(''' cd %(server_project_dir)s/src/;
            git prune;
            git gc --aggressive;
            git repack -a -d --depth=250 --window=250;
        ''' % env)


@task
def upgrade():
    """
    Upgrade a pip package
    """
    prompt('package name:', 'package_name')
    # remove the build directory of the package and upgrade
    run('''rm -rf %(environment_dir)sbuild/%(package_name)s;
           source %(environment_dir)sbin/activate;
           pip install %(package_name)s --upgrade''' % env)

