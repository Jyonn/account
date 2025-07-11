import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import html

from smartdjango import Error

from Config.models import Config, CI
from User.models import User
from account.settings import PROJ_INIT

if PROJ_INIT:
    SENDER_EMAIL = CI.SENDER_EMAIL
    SENDER_EMAIL_PWD = CI.SENDER_EMAIL_PWD
    SMTP_SERVER = CI.SMTP_SERVER
    SMTP_PORT = CI.SMTP_PORT
else:
    SENDER_EMAIL = Config.get_value_by_key(CI.SENDER_EMAIL)
    SENDER_EMAIL_PWD = Config.get_value_by_key(CI.SENDER_EMAIL_PWD)
    SMTP_SERVER = Config.get_value_by_key(CI.SMTP_SERVER)
    SMTP_PORT = int(Config.get_value_by_key(CI.SMTP_PORT))


try:
    ROOT_USER = User.get_by_id(1).body
except Exception:
    pass


class Element:
    def __init__(self, text, escape=True):
        self.text = html.escape(text) if escape else text

    def bold(self, title=False):
        if title:
            self.text = '<span style="font-weight:bold;">' + self.text + '</span>'
        else:
            self.text = '<span style="font-weight:bold;color:#5F80D0;">' + self.text + '</span>'
        return self

    def link(self, link):
        self.text = '<a href="' + link + '" style="color:#FFB500;">' + self.text + '</a>'
        return self

    def a(self, element):
        self.text += element.text
        return self


@Error.register
class EmailErrors:
    SEND_EMAIL_ERROR = Error("邮件发送错误")
    EMAIL_NOT_EXIST = Error("不存在邮箱")


class Email:
    template = '''
    <div style="padding:0;margin:0;box-sizing:border-box;width:100%;display:flex;justify-content:center;background:#F8F8F8;">
     <div style="width:500px;position:relative;">
      <div style="height:50px;line-height:50px;width:100%;">
       <div style="color:#999999;padding:0 20px;font-size:12px;">以下内容为齐天簿自动发送</div>
      </div>
      <div>
       <div style="position:relative;border-radius:10px;background:white;padding:50px;">
        <div style="color:black;font-size:36px;padding-bottom:20px;">{subject}</div>
        <div style="color:#888888;font-size:16px;">{dear}</div>
        <div style="color:#888888;font-size:16px;padding:10px 20px">{content}</div>
       </div>
      </div>
      <div style="height:50px;line-height:50px;width:100%;">
       <div style="color:#999999;padding:0 20px;font-size:12px;">连接世界，看见精彩 | <a href="https://sso.6-79.cn" style="color:#FFB500;">齐天簿</a></div>
      </div>
     </div>
    </div>'''

    def __init__(self, user, subject, dear, content):
        self.user = user
        self.subject = subject
        self.dear = dear
        self.content = content

    def output(self):
        return self.template.format(
            subject=self.subject,
            dear=self.dear.text,
            content=self.content.text
        )

    @staticmethod
    def _send(email):
        try:
            msg = MIMEText(email.output(), 'html', 'utf-8')
            msg['From'] = formataddr(['齐天簿云服务', SENDER_EMAIL])
            msg['To'] = formataddr([email.user.nickname or '齐天簿用户', email.user.email])
            msg['Subject'] = '【齐天簿】' + email.subject

            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.login(SENDER_EMAIL, SENDER_EMAIL_PWD)
            server.sendmail(SENDER_EMAIL, [email.user.email], msg.as_string())
            server.quit()
        except Exception:
            raise EmailErrors.SEND_EMAIL_ERROR

    def send(self):
        return Email._send(self)

    @staticmethod
    def developer_apply(user, link):
        if not ROOT_USER.email:
            raise EmailErrors.EMAIL_NOT_EXIST
        return Email(
            subject='开发者申请',
            dear=Element('你好，管理员：'),
            content=Element('用户')
            .a(Element(user.nickname or '齐天簿用户').bold())
            .a(Element('已提交了开发者申请，请'))
            .a(Element('点击链接').link(link))
            .a(Element('进行审核！')),
            user=ROOT_USER,
        ).send()

    @staticmethod
    def real_verify(user, link):
        if not ROOT_USER.email:
            raise EmailErrors.EMAIL_NOT_EXIST
        return Email(
            subject='实名认证',
            dear=Element('你好，管理员：'),
            content=Element('用户')
            .a(Element(user.nickname or '齐天簿用户').bold())
            .a(Element('已提交了实名认证，请'))
            .a(Element('点击链接').link(link))
            .a(Element('进行审核！')),
            user=ROOT_USER,
        ).send()

    @staticmethod
    def app_msg(user_app, message):
        if not user_app.user.email:
            raise EmailErrors.EMAIL_NOT_EXIST
        return Email(
            subject='应用推送消息',
            dear=Element('你好，')
            .a(Element(user_app.user.nickname or '齐天簿用户').bold())
            .a(Element('：')),
            content=Element('您授权的应用')
            .a(Element(user_app.app.name).bold())
            .a(Element('给您发送一则消息：\n'))
            .a(Element(message)),
            user=user_app.user,
        ).send()

    @staticmethod
    def email_verify(user, code):
        return Email(
            subject='邮件验证',
            dear=Element('你好，')
            .a(Element(user.nickname or '齐天簿用户').bold())
            .a(Element('：')),
            content=Element('您的邮箱验证码为')
            .a(Element(code).bold())
            .a(Element('，或点击此处通过验证。如果您从未使用齐天簿应用，请忽略此邮件。')),
            user=user,
        ).send()
