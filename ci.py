from flask import Flask, request, abort
from hashlib import sha1
import hmac
import os

app = Flask(__name__)


@app.route('/', methods=['POST'])
def root():
    if confirm_payload(request):
        handle_github_request(request.get_json(force=True))
        pass
    else:
        abort(403)


def handle_github_request(req):
    # update from git repository
    # restart the jovabot service
    pass


def confirm_payload(payload):
    hashed = hmac.new(os.environ('CI_JOVABOT_SECRET_TOKEN'), payload, sha1)
    return hmac.compare_digest(hashed.hexdigest(), payload.headers['X-Hub-Signature'])


if __name__ == '__main__':
    app.run()
