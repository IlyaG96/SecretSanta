from fabric.contrib.files import exists
from fabric.api import cd, local, run, env, hosts, sudo

REPO_URL = 'git@github.com:IlyaG96/SecretSanta.git'

@hosts(['137.184.45.165'])
def deploy():
    site_folder = f'/home/django/code/SecretSanta'
    run(f'mkdir -p {site_folder}')
    with cd(site_folder):
        _get_latest_source()
        _update_virtualenv()
        _update_database()
        _daemon_reload()
        _get_latest_source()


def _get_latest_source():
    if exists('.git'):
        run('git pull')
    else:
        run(f'git clone {REPO_URL} .')
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run(f'git reset --hard {current_commit}')


def _update_virtualenv():
    if not exists('env/bin/pip'):
        run(f'python3 -m venv env')
    run('./env/bin/pip install -r requirements.txt')


def echo_git_pull():
    msg = run('echo | git pull')
    print(msg)


def _update_static_files():
    run('./env/bin/python manage.py collectstatic --noinput')


def _update_database():
    run('./env/bin/python manage.py migrate --noinput')


def _daemon_reload():
    run('sudo systemctl daemon-reload', shell=False)



