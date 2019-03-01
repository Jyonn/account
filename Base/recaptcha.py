import requests

from Config.models import Config
from Base.common import deprint

G_RECAPTCHA_SECRET = Config.get_value_by_key('g-recaptcha-secret', 'YOUR-G_RECAPTCHA-SECRET').body


class Recaptcha:
    API_URL = 'https://recaptcha.net/recaptcha/api/siteverify'

    @staticmethod
    def verify(response):
        try:
            resp = requests.post(Recaptcha.API_URL, {
                'secret': G_RECAPTCHA_SECRET,
                'response': response,
            })
            success = resp.json()['success']
        except Exception as err:
            deprint(str(err))
            return False
        return success
