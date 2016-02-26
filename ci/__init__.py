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
import sys
import codecs
import socket
import json

app = Flask(__name__)
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                    level=logging.DEBUG,
                    format='%(asctime)-15s|%(levelname)-8s|'
                           '%(process)d|%(name)s|%(module)s|%(funcName)s::%(lineno)d|%(message)s')


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
    # update from git repository
    g = git.cmd.Git(os.environ['GIT_DIR'])
    git_ret = g.pull('origin', os.environ['BRANCH_TO_UPDATE'])
    service_ret = None
    if any_file_changed(req):
        # restart the jovabot service
        service_ret = subprocess.call(['sudo', '/usr/sbin/service', 'jovabot', 'restart'], shell=False)
    # I know, it sucks
    time.sleep(1)
    # dispatch the channel update to jovabot
    update_ret = jovabot_channel_update(req)
    return update_ret, git_ret, service_ret


def confirm_payload(payload):
    ba = bytes(os.environ['CI_JOVABOT_SECRET_TOKEN'], encoding='utf-8')
    hashed = hmac.new(ba, payload.data, sha1)
    return hmac.compare_digest('sha1=' + hashed.hexdigest(), payload.headers['X-Hub-Signature'])


def any_file_changed(req):
    changed = 0
    if check_for_master_branch(req):
        for commit in req.get('commits'):
            file_list = commit.get('added') + commit.get('removed') + commit.get('modified')
            logging.info(file_list)
            changed += find_file_with_exts(file_list)
    logging.info('nr of files changed {}'.format(changed))
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
        d = json.dumps(req)
        logging.debug(d)
        return requests.post('https://{}/{}'.format(endpoint, os.environ['UPDATE_SECRET']), json=d)


def check_for_master_branch(req):
    ref = req.get('ref')
    if ref and os.environ['BRANCH_TO_UPDATE'] in ref:
        return ref
    return None


if __name__ == '__main__':
    app.run()
