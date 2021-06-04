""" 180228 Adel Liu

七牛上传政策
"""
from Base.common import HOST
from account.settings import MAX_IMAGE_SIZE


AVATAR_CALLBACK = '%s/user/avatar' % HOST
LOGO_CALLBACK = '%s/app/logo' % HOST
VERIFY_FRONT_CALLBACK = '%s/user/idcard?back=0' % HOST
VERIFY_BACK_CALLBACK = '%s/user/idcard?back=1' % HOST

BASE_IMAGE_POLICY = dict(
    insertOnly=1,
    callbackBodyType='application/json',
    fsizeMin=1,
    fsizeLimit=MAX_IMAGE_SIZE,
    mimeLimit='image/*',
)

AVATAR_POLICY = dict(
    callbackUrl=AVATAR_CALLBACK,
)
AVATAR_POLICY.update(BASE_IMAGE_POLICY)

LOGO_POLICY = dict(
    callbackUrl=LOGO_CALLBACK,
)
LOGO_POLICY.update(BASE_IMAGE_POLICY)

VERIFY_FRONT_POLICY = dict(
    callbackUrl=VERIFY_FRONT_CALLBACK,
)
VERIFY_FRONT_POLICY.update(BASE_IMAGE_POLICY)

VERIFY_BACK_POLICY = dict(
    callbackUrl=VERIFY_BACK_CALLBACK,
)
VERIFY_BACK_POLICY.update(BASE_IMAGE_POLICY)


class Policy:
    @staticmethod
    def avatar(user_id):

        policy = dict(
            callbackBody='{"key":"$(key)","user_id":"%s"}' % user_id
        )
        policy.update(AVATAR_POLICY)
        return policy

    @staticmethod
    def logo(app_id):
        policy = dict(
            callbackBody='{"key":"$(key)","app_id":"%s"}' % app_id
        )
        policy.update(LOGO_POLICY)
        return policy

    @staticmethod
    def verify_front(user_id):
        policy = dict(
            callbackBody='{"key":"$(key)","user_id":"%s"}' % user_id
        )
        policy.update(VERIFY_FRONT_POLICY)
        return policy

    @staticmethod
    def verify_back(user_id):
        policy = dict(
            callbackBody='{"key":"$(key)","user_id":"%s"}' % user_id
        )
        policy.update(VERIFY_BACK_POLICY)
        return policy
