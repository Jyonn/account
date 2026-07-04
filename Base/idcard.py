import datetime

from qcloud_image import CIUrls
from qcloud_image import Client
from smartdjango import Error

from Config.models import CI, Config

APP_ID = Config.get_value_by_key(CI.QCLOUD_APP_ID)
SECRET_ID = Config.get_value_by_key(CI.QCLOUD_SECRET_ID)
SECRET_KEY = Config.get_value_by_key(CI.QCLOUD_SECRET_KEY)

BUCKET = 'BUCKET'
client = Client(APP_ID, SECRET_ID, SECRET_KEY, BUCKET)
client.use_http()
client.set_timeout(30)


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
        payload = IDCard._extract_payload(client.idcard_detect(CIUrls([link]), 0))

        try:
            birth = IDCard._parse_date_str(IDCard._field_value(payload.get('birth') or payload.get('Birth')))
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR('生日验证错误', debug_message=err)

        return dict(
            male=IDCard._parse_gender(IDCard._field_value(payload.get('sex') or payload.get('Sex'))),
            name=IDCard._field_value(payload.get('name') or payload.get('Name')),
            idcard=IDCard._field_value(payload.get('id') or payload.get('IdNum')),
            birthday=birth,
        )

    @staticmethod
    def detect_back(link):
        payload = IDCard._extract_payload(client.idcard_detect(CIUrls([link]), 1))
        valid_date = IDCard._field_value(payload.get('valid_date') or payload.get('ValidDate'))

        try:
            valid_start, valid_end = IDCard._parse_valid_date(valid_date)
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR('有效期验证错误', debug_message=err)

        return dict(
            valid_start=valid_start,
            valid_end=valid_end,
        )

    @staticmethod
    def _extract_payload(resp):
        if not isinstance(resp, dict):
            raise IDCardErrors.IDCARD_DETECT_ERROR('身份证识别返回格式异常', debug_message=resp)

        response = resp.get('Response')
        if isinstance(response, dict):
            error = response.get('Error')
            if error:
                raise IDCardErrors.IDCARD_DETECT_ERROR(
                    error.get('Message') or error.get('Code') or '腾讯云身份证识别失败',
                    debug_message=resp,
                )
            return response

        httpcode = resp.get('httpcode')
        result_list = resp.get('result_list')
        if isinstance(result_list, list) and result_list:
            item = result_list[0]
            if httpcode is not None and httpcode != 200:
                raise IDCardErrors.IDCARD_DETECT_ERROR(
                    item.get('message') or resp.get('message') or '腾讯云身份证识别失败',
                    debug_message=resp,
                )
            if item.get('code') != 0:
                raise IDCardErrors.IDCARD_DETECT_ERROR(
                    item.get('msg') or item.get('message') or '腾讯云身份证识别失败',
                    debug_message=resp,
                )
            return item.get('data') or {}

        # 兼容直接返回 OCR 字段的响应结构
        if any(key in resp for key in ['Name', 'Birth', 'IdNum', 'ValidDate', 'name', 'birth', 'id', 'valid_date']):
            return resp

        if httpcode is not None and httpcode != 200:
            raise IDCardErrors.IDCARD_DETECT_ERROR(
                resp.get('message') or resp.get('msg') or f'腾讯云身份证识别失败({httpcode})',
                debug_message=resp,
            )

        raise IDCardErrors.IDCARD_DETECT_ERROR('身份证识别返回格式异常', debug_message=resp)

    @staticmethod
    def _parse_date_str(value):
        if not value:
            raise ValueError('empty date')

        normalized = str(value).strip()
        for splitter in ['年', '月', '.','/','-']:
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
        raise IDCardErrors.IDCARD_DETECT_ERROR('性别识别结果异常', debug_message=value)

    @staticmethod
    def _field_value(value):
        if isinstance(value, dict):
            for key in ['String', 'Value', 'Text']:
                if key in value:
                    return value[key]
        return value
