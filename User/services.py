import datetime

from Base.auth import Auth
from Base.idcard import IDCard, IDCardErrors
from Base.jtoken import JWType, JWT
from Base.mail import Email
from Base.policy import Policy
from Base.premise_checker import PremiseCheckerErrors
from Base.qn import qn_public_manager, qn_res_manager
from Base.send_mobile import SendMobile
from Base.session import Session, SessionErrors
from User.models import User
from User.validators import UserErrors


class UserAccountService:
    @staticmethod
    def get_phone_status(phone):
        try:
            User.get_by_phone(phone)
            registered = True
        except UserErrors.USER_NOT_FOUND:
            registered = False

        return dict(registered=registered, phone=phone)

    @staticmethod
    def ensure_qitian_exists(qitian):
        User.get_by_qitian(qitian)
        return dict(exists=True, qitian=qitian)

    @staticmethod
    def get_profile(user, request_type):
        return user.d_oauth() if request_type == JWType.AUTH_TOKEN else user.d()

    @staticmethod
    def register(request, password, code):
        phone = SendMobile.check_captcha(request, code)
        user = User.create(phone, password)
        return Auth.get_login_token(user)

    @staticmethod
    def update_profile(user, payload):
        user.modify_info(**payload)
        return user.d()

    @staticmethod
    def get_phone(user):
        return user.phone

    @staticmethod
    def login_from_session(request, password):
        login_type = Session.load(request, SendMobile.LOGIN_TYPE, once_delete=False)
        if not login_type:
            raise SessionErrors.SESSION

        login_value = Session.load(request, login_type, once_delete=False)
        if not login_value:
            raise SessionErrors.SESSION

        if login_type == SendMobile.PHONE_NUMBER:
            user = User.authenticate(None, login_value, password)
        else:
            user = User.authenticate(login_value, None, password)
        return Auth.get_login_token(user)

    @staticmethod
    def get_avatar_upload_token(user, filename):
        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/avatar/%s/%s' % (user.user_str_id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.avatar(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    def update_avatar(user, key):
        user.modify_avatar(key)
        return user.d()

    @staticmethod
    def apply_developer(user):
        if user.verify_status != User.VERIFY_STATUS_DONE:
            return PremiseCheckerErrors.REQUIRE_REAL_VERIFY
        user.developer()
        return user.d()


class UserVerificationService:
    @staticmethod
    def get_idcard_upload_token(user, filename, back):
        UserVerificationService.ensure_unverified(
            user,
            verifying_message='无法重新上传',
            verified_message='无法重新上传',
        )

        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/card/%s/%s/%s' % (
            user.user_str_id,
            ['front', 'back'][back],
            crt_time,
            filename,
        )
        policy = Policy.verify_back if back else Policy.verify_front
        qn_token, key = qn_res_manager.get_upload_token(key, policy(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    def update_idcard_image(user, key, back):
        UserVerificationService.ensure_unverified(
            user,
            verifying_message='无法重新上传',
            verified_message='无法重新上传',
        )
        if back:
            return user.upload_verify_back(key)
        return user.upload_verify_front(key)

    @staticmethod
    def auto_verify(user):
        UserVerificationService.ensure_unverified(
            user,
            verifying_message='无法继续识别',
            verified_message='无法继续识别',
        )

        urls = user.get_card_urls()
        if not urls['front'] or not urls['back']:
            raise IDCardErrors.CARD_NOT_COMPLETE

        front_info = IDCard.detect_front(urls['front'])
        back_info = IDCard.detect_back(urls['back'])

        back_info.update(front_info)
        back_info['type'] = 'idcard-verify'
        back_info['user_id'] = user.user_str_id
        token, verify_info = JWT.encrypt(back_info, expire_second=60 * 5)
        verify_info['token'] = token
        user.update_verify_type(User.VERIFY_CHINA)
        return verify_info

    @staticmethod
    def confirm_verify(user, payload, required_keys):
        UserVerificationService.ensure_unverified(
            user,
            verifying_message='无法继续确认',
            verified_message='无法继续确认',
        )

        if payload['auto']:
            dict_ = JWT.decrypt(payload['token'])
            if 'user_id' not in dict_:
                raise IDCardErrors.AUTO_VERIFY_FAILED
            if user.user_str_id != dict_['user_id']:
                raise IDCardErrors.AUTO_VERIFY_FAILED

            crt_time = datetime.datetime.now().timestamp()
            valid_start = datetime.datetime.strptime(dict_['valid_start'], '%Y-%m-%d').timestamp()
            valid_end = datetime.datetime.strptime(dict_['valid_end'], '%Y-%m-%d').timestamp()
            if valid_start > crt_time or crt_time > valid_end:
                raise IDCardErrors.CARD_VALID_EXPIRED

            user.update_card_info(
                dict_['name'],
                dict_['male'],
                dict_['idcard'],
                datetime.datetime.strptime(dict_['birthday'], '%Y-%m-%d').date(),
            )
            user.update_verify_status(User.VERIFY_STATUS_DONE)
            return user.d()

        for key in required_keys:
            if not payload[key]:
                return UserErrors.MISSING(key)

        user.update_card_info(
            real_name=payload['name'],
            birthday=payload['birthday'],
            idcard=payload['idcard'],
            male=payload['male'],
        )
        user.update_verify_status(User.VERIFY_STATUS_UNDER_MANUAL)
        Email.real_verify(user, '')
        return user.d()

    @staticmethod
    def ensure_unverified(user, verifying_message, verified_message):
        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status in (User.VERIFY_STATUS_UNDER_AUTO, User.VERIFY_STATUS_UNDER_MANUAL):
                raise IDCardErrors.VERIFYING(verifying_message)
            raise IDCardErrors.REAL_VERIFIED(verified_message)
