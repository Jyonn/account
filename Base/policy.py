""" 180228 Adel Liu

七牛上传政策
"""
from account.settings import MAX_IMAGE_SIZE, HOST

AVATAR_CALLBACK = '%s/api/user/avatar' % HOST

AVATAR_POLICY = dict(
    insertOnly=1,
    callbackUrl=AVATAR_CALLBACK,
    callbackBodyType='application/json',
    fsizeMin=1,
    fsizeLimit=MAX_IMAGE_SIZE,
    mimeLimit='image/*',
)


def get_avatar_policy(user_id):
    policy = AVATAR_POLICY
    policy['callbackBody'] = '{"key":"$(key)","user_id":%s}' % user_id
    return policy
