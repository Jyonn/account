import datetime
import json

from smartdjango import Error
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import models, ocr_client

from Config.models import CI, Config

SECRET_ID = Config.get_value_by_key(CI.QCLOUD_SECRET_ID)
SECRET_KEY = Config.get_value_by_key(CI.QCLOUD_SECRET_KEY)
OCR_REGION = 'ap-guangzhou'
OCR_ENDPOINT = 'ocr.tencentcloudapi.com'


@Error.register
class IDCardErrors:
    IDCARD_DETECT_ERROR = Error("身份证自动验证错误")
    REAL_VERIFIED = Error("已实名认证")
    CARD_NOT_COMPLETE = Error("身份证正反面照片没有完善")
    CARD_VALID_EXPIRED = Error("身份证认证过期")
    AUTO_VERIFY_FAILED = Error("自动实名认证失败，请尝试人工认证")
    VERIFYING = Error("您已提交认证")


class IDCard:
    @staticmethod
    def detect_front(link):
        response, payload = IDCard._request('FRONT', link)

        try:
            birth = IDCard._parse_date_str(response.Birth)
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=f'生日验证错误: {err}')

        try:
            male = IDCard._parse_gender(response.Sex)
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=f'性别验证错误: {err}')

        name = (response.Name or '').strip()
        idcard = (response.IdNum or '').strip()
        if not name or not idcard:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=payload)

        return dict(
            male=male,
            name=name,
            idcard=idcard,
            birthday=birth,
        )

    @staticmethod
    def detect_back(link):
        response, payload = IDCard._request('BACK', link)

        try:
            valid_start, valid_end = IDCard._parse_valid_date(response.ValidDate)
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=f'有效期验证错误: {err}')

        if not valid_start or not valid_end:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=payload)

        return dict(
            valid_start=valid_start,
            valid_end=valid_end,
        )

    @staticmethod
    def _request(card_side, link):
        request = models.IDCardOCRRequest()
        request.from_json_string(json.dumps({
            'ImageUrl': link,
            'CardSide': card_side,
        }))

        try:
            response = IDCard._client().IDCardOCR(request)
        except TencentCloudSDKException as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=str(err))
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details=err)

        payload = json.loads(response.to_json_string())
        return response, payload

    @staticmethod
    def _client():
        if not SECRET_ID or not SECRET_KEY:
            raise IDCardErrors.IDCARD_DETECT_ERROR(details='缺少腾讯云 OCR 配置')

        cred = credential.Credential(SECRET_ID, SECRET_KEY)
        http_profile = HttpProfile()
        http_profile.endpoint = OCR_ENDPOINT

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        return ocr_client.OcrClient(cred, OCR_REGION, client_profile)

    @staticmethod
    def _parse_date_str(value):
        if not value:
            raise ValueError('empty date')

        normalized = str(value).strip()
        for splitter in ['年', '月', '.', '/', '-']:
            normalized = normalized.replace(splitter, '-')
        normalized = normalized.replace('日', '')
        normalized = normalized.replace('--', '-')
        normalized = normalized.strip('-')

        for fmt in ['%Y-%m-%d', '%Y%m%d']:
            try:
                return datetime.datetime.strptime(normalized, fmt).strftime('%Y-%m-%d')
            except ValueError:
                pass

        digits = ''.join(filter(str.isdigit, normalized))
        if len(digits) == 8:
            return datetime.datetime.strptime(digits, '%Y%m%d').strftime('%Y-%m-%d')

        raise ValueError(normalized)

    @staticmethod
    def _parse_valid_date(value):
        if not value:
            raise ValueError('empty valid_date')

        normalized = str(value).strip()
        normalized = normalized.replace('至', '-').replace('_', '-').replace('—', '-').replace('－', '-')
        parts = [part.strip() for part in normalized.split('-') if part.strip()]
        if len(parts) < 2:
            raise ValueError(normalized)

        valid_start = IDCard._parse_date_str(parts[0])
        valid_end = '2099-12-31' if parts[1] in ['长期', '长', 'LONG_TERM'] else IDCard._parse_date_str(parts[1])
        return valid_start, valid_end

    @staticmethod
    def _parse_gender(value):
        if value in [True, False]:
            return value

        normalized = str(value).strip().lower()
        if normalized in ['男', 'male', 'm', '1', 'true']:
            return True
        if normalized in ['女', 'female', 'f', '0', 'false']:
            return False
        raise ValueError(normalized)
