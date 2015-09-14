from flask import Flask, request, abort
from hashlib import sha1
import hmac
import os
import git
import subprocess

app = Flask(__name__)


# CONFIGURATION
GIT_DIR = '/home/acco/dev/jovabot/'


@app.route('/', methods=['POST'])
def root():
    if confirm_payload(request):
        handle_github_request(request.get_json(force=True))
    else:
        abort(403)


def handle_github_request(req):
    # update from git repository
    g = git.cmd.Git(GIT_DIR)
    git_ret = g.pull('origin', 'develop')
    # restart the jovabot service
    service_ret = subprocess.call(['/usr/sbin/service', 'jovabot', 'restart'], shell=False)
    return git_ret, service_ret


def confirm_payload(payload):
    hashed = hmac.new(os.environ('CI_JOVABOT_SECRET_TOKEN'), payload, sha1)
    return hmac.compare_digest(hashed.hexdigest(), payload.headers['X-Hub-Signature'])


if __name__ == '__main__':
    app.run()
