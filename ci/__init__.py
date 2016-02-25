from flask import Flask, request
from hashlib import sha1
import hmac
import os
import git
import subprocess
import logging
import array
import requests
import time

app = Flask(__name__)
logging.basicConfig(filename='ci_jovabot.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

# CONFIGURATION
GIT_DIR = '/home/acco/dev/jovabot/'


@app.route('/', methods=['POST'])
def root():
    logging.debug('Received request')
    if confirm_payload(request):
        u, g, s = handle_github_request(request.get_json(force=True))
        logging.info('Received payload from github => u[{}] g[{}] s[{}]'.format(u, g, s))
    else:
        logging.debug('Request not valid')
        return 'ko', 403
    return 'ok', 200


def handle_github_request(req):
    # dispatch the channel update to jovabot
    update_ret = jovabot_channel_update(req)
    # I know, it sucks
    time.sleep(1)
    # update from git repository
    g = git.cmd.Git(GIT_DIR)
    git_ret = g.pull('origin', 'master')
    service_ret = None
    if any_file_changed(req):
        # restart the jovabot service
        service_ret = subprocess.call(['sudo', '/usr/sbin/service', 'jovabot', 'restart'], shell=False)
    return update_ret, git_ret, service_ret


def confirm_payload(payload):
    ba = bytes(os.environ['CI_JOVABOT_SECRET_TOKEN'], encoding='utf-8')
    hashed = hmac.new(ba, payload.data, sha1)
    return hmac.compare_digest('sha1=' + hashed.hexdigest(), payload.headers['X-Hub-Signature'])


def any_file_changed(req):
    changed = 0
    if check_for_master_branch(req):
        hc = req.get('head_commit')
        if hc:
            file_list = hc.get('added') + hc.get('removed') + hc.get('modified')
            changed = find_file_with_exts(file_list)
    return changed > 0


def find_file_with_exts(file_list, ext=None):
    if ext is None:
        ext = ['.py']
    c = 0
    if file_list:
        for file in file_list:
            if file.endswith(tuple(ext)):
                c = c + 1
    return c


def jovabot_channel_update(req):
    if check_for_master_branch(req):
        endpoint = socket.gethostname() + '/' + os.environ['JOVABOT_WEBAPP_NAME'] + '/channel-update'
        return requests.post('{}/{}'.format(endpoint, os.environ('UPDATE_SECRET'), data=req.get('commits')))


def check_for_master_branch(req):
    ref = req.get('ref')
    if ref and 'master' in ref:  # only updates on master
        return ref
    return None


if __name__ == '__main__':
    app.run()
