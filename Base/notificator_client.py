from notificator import Notificator

from Config.models import CI, Config


class NotificatorClient:
    ADMIN_VERIFY_EMAIL = 'liu@qijiong.work'

    @staticmethod
    def client():
        return Notificator(
            name=Config.get_value_by_key(CI.NOTIFICATOR_NAME),
            token=Config.get_value_by_key(CI.NOTIFICATOR_TOKEN),
            host=Config.get_value_by_key(CI.NOTIFICATOR_HOST),
        )

    @staticmethod
    def send_real_verify_notice(user):
        title = '齐天簿有新的实名认证待审核'
        body = '\n'.join([
            '有用户提交了新的实名认证资料，请尽快人工检验。',
            f'用户ID：{user.user_str_id}',
            f'齐天号：{user.qitian or "未设置"}',
            f'昵称：{user.nickname or "未设置"}',
            f'手机号：{user.phone or "未绑定"}',
        ])
        return NotificatorClient.client().prepare_mail(
            NotificatorClient.ADMIN_VERIFY_EMAIL,
            recipient_name='管理员',
        ).send(
            format='text',
            title=title,
            body=body,
        )
