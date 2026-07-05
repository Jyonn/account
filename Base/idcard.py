from smartdjango import Error


@Error.register
class IDCardErrors:
    IDCARD_DETECT_ERROR = Error("身份证自动验证错误")
    MANUAL_VERIFY_ONLY = Error("当前仅支持人工审核")
    REAL_VERIFIED = Error("已实名认证")
    CARD_NOT_COMPLETE = Error("身份证正反面照片没有完善")
    CARD_VALID_EXPIRED = Error("身份证认证过期")
    AUTO_VERIFY_FAILED = Error("自动实名认证失败，请尝试人工认证")
    VERIFYING = Error("您已提交认证")
