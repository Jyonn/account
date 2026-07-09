from django.views import View
from smartdjango import Code, Error, analyse, Validator

from Base.auth import Auth, Request
from User.models import CLIDeviceGrant


CLI_VERIFICATION_URI = 'https://qt.6-79.cn/cli'


@Error.register
class AuthCLIErrors:
    DEVICE_NOT_FOUND = Error('不存在的 CLI 登录请求', code=Code.NotFound)
    DEVICE_EXPIRED = Error('CLI 登录请求已过期', code=Code.BadRequest)
    AUTHORIZATION_PENDING = Error('等待网页端确认', code=Code.BadRequest)
    AUTHORIZATION_DENIED = Error('网页端已拒绝此次授权', code=Code.BadRequest)
    AUTHORIZATION_CONSUMED = Error('此次授权已被使用', code=Code.BadRequest)
    INVALID_DECISION = Error('不支持的授权操作', code=Code.BadRequest)


class AuthCLIBaseView(View):
    @staticmethod
    def get_device_grant_by_device_code(device_code):
        try:
            return CLIDeviceGrant.get_by_device_code(device_code)
        except CLIDeviceGrant.DoesNotExist:
            raise AuthCLIErrors.DEVICE_NOT_FOUND

    @staticmethod
    def get_device_grant_by_user_code(user_code):
        normalized = CLIDeviceGrant.normalize_user_code(user_code)
        if not normalized:
            raise AuthCLIErrors.DEVICE_NOT_FOUND

        for grant in CLIDeviceGrant.objects.order_by('-create_time'):
            if CLIDeviceGrant.normalize_user_code(grant.user_code) == normalized:
                return grant
        raise AuthCLIErrors.DEVICE_NOT_FOUND

    @staticmethod
    def ensure_active(grant: CLIDeviceGrant):
        if grant.is_expired():
            raise AuthCLIErrors.DEVICE_EXPIRED
        return grant

    @staticmethod
    def serialize_grant(grant: CLIDeviceGrant):
        return dict(
            user_code=grant.user_code,
            client_name=grant.client_name,
            status=grant.status_key(),
            expires_in=grant.expires_in(),
        )


class AuthCLIDeviceStartView(AuthCLIBaseView):
    @analyse.json(
        Validator('client_name', '客户端名称').null().default('qt-cli'),
        restrict_keys=False,
    )
    def post(self, request):
        client_name = (request.json.client_name or 'qt-cli').strip() or 'qt-cli'
        grant = CLIDeviceGrant.create_grant(client_name=client_name)
        return dict(
            device_code=grant.device_code,
            user_code=grant.user_code,
            verification_uri=CLI_VERIFICATION_URI,
            verification_uri_complete=f'{CLI_VERIFICATION_URI}?code={grant.user_code}',
            expires_in=grant.expires_in(),
            interval=grant.interval,
        )


class AuthCLIDevicePollView(AuthCLIBaseView):
    @analyse.json(
        Validator('device_code', '设备码'),
        restrict_keys=False,
    )
    def post(self, request):
        grant = self.ensure_active(self.get_device_grant_by_device_code(request.json.device_code))

        if grant.status == CLIDeviceGrant.STATUS_PENDING:
            raise AuthCLIErrors.AUTHORIZATION_PENDING
        if grant.status == CLIDeviceGrant.STATUS_DENIED:
            raise AuthCLIErrors.AUTHORIZATION_DENIED
        if grant.status == CLIDeviceGrant.STATUS_CONSUMED:
            raise AuthCLIErrors.AUTHORIZATION_CONSUMED

        payload = Auth.get_login_token(grant.user)
        grant.consume()
        return payload


class AuthCLIDeviceView(AuthCLIBaseView):
    @analyse.query(
        Validator('user_code', '用户确认码'),
    )
    @Auth.require_login(deny_auth_token=True)
    def get(self, request: Request):
        grant = self.ensure_active(self.get_device_grant_by_user_code(request.query.user_code))
        return self.serialize_grant(grant)


class AuthCLIDeviceConfirmView(AuthCLIBaseView):
    @analyse.json(
        Validator('user_code', '用户确认码'),
        Validator('decision', '授权决定').default('approve'),
        restrict_keys=False,
    )
    @Auth.require_login(deny_auth_token=True)
    def post(self, request: Request):
        grant = self.ensure_active(self.get_device_grant_by_user_code(request.json.user_code))
        decision = request.json.decision

        if decision == 'approve':
            grant.approve(request.user)
        elif decision == 'deny':
            grant.deny()
        else:
            raise AuthCLIErrors.INVALID_DECISION

        return self.serialize_grant(grant)
