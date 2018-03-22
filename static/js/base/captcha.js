function captchaHandler({captchaObj, bindBtnId, phoneInputId, regionId, type, successCallback}) {
    let bindBtn = document.getElementById(bindBtnId);
    let phoneInput = document.getElementById(phoneInputId);
    let region = document.getElementById(regionId);
    let captchaVerify = function () {
        captchaObj.verify();
    };

    bindBtn.addEventListener('click', captchaVerify);
    captchaObj.onSuccess(function () {
        let result = captchaObj.getValidate();
        if (!result) {
            return InfoCenter.push(new Info("请完成验证", Info.TYPE_WARN));
        }
        let phone = region.innerText + phoneInput.value;
        Service.verifyCaptchaAPI({
            challenge: result.geetest_challenge,
            validate: result.geetest_validate,
            seccode: result.geetest_seccode,
            phone: phone,
            type: type,
        })
            .then(() => {
                bindBtn.removeEventListener('click', captchaVerify);
                successCallback();
            })
            .catch(() => {
                window.reload();
            });
    })
}