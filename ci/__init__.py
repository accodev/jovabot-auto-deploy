from flask import Flask, request, abort
from hashlib import sha1
import hmac
import os
import git
import subprocess
import logging
import array

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
    if confirm_payload(request):
        handle_github_request(request.get_json(force=True))
    else:
        abort(403)
    return 'ok', 200


def handle_github_request(req):
    # update from git repository
    g = git.cmd.Git(GIT_DIR)
    git_ret = g.pull('origin', 'develop')
    # restart the jovabot service
    service_ret = subprocess.call(['sudo', '/usr/sbin/service', 'jovabot', 'restart'], shell=False)
    return git_ret, service_ret


def confirm_payload(payload):
    ba = bytes(os.environ['CI_JOVABOT_SECRET_TOKEN'], encoding='utf-8')
    hashed = hmac.new(ba, payload.data, sha1)
    return hmac.compare_digest('sha1=' + hashed.hexdigest(), payload.headers['X-Hub-Signature'])


if __name__ == '__main__':
    app.run()
