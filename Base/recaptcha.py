import requests

from Config.models import Config, CI

G_RECAPTCHA_SECRET = Config.get_value_by_key(CI.G_RECAPTCHA_SECRET)


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
        except Exception:
            return False
        return success
