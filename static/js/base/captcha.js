function captchaHandler({captchaObj, bindBtnId, phoneInputId, qitianInputId, regionId, type, successCallback}) {
    let bindBtn = document.getElementById(bindBtnId);
    let phoneInput = document.getElementById(phoneInputId);
    let region = document.getElementById(regionId);
    let qitianInput;
    if (qitianInputId) {
        qitianInput = document.getElementById(qitianInputId);
    }
    let captchaVerify = function () {
        if (type === -1) {
            if (Login.loginType === Login.loginWithPhone && !phoneInput.value) {
                InfoCenter.push(new Info('手机号不允许为空'));
                return;
            }
            if (Login.loginType === Login.loginWithQitian && !qitianInput.value) {
                InfoCenter.push(new Info('齐天号不允许为空'));
                return;
            }
        } else if (!phoneInput.value) {
            InfoCenter.push(new Info('手机号不允许为空'));
            return;
        }
        captchaObj.verify();
    };

    bindBtn.addEventListener('click', captchaVerify);
    captchaObj.onSuccess(function () {
        let result = captchaObj.getValidate(), account;
        if (!result) {
            return InfoCenter.push(new Info("请完成验证", Info.TYPE_WARN));
        }
        account = region.innerText + phoneInput.value;
        if (type === -1 && Login.loginType === Login.loginWithQitian) {
            account = qitianInput.value;
            type = -2;
        }
        Service.verifyCaptchaAPI({
            challenge: result.geetest_challenge,
            validate: result.geetest_validate,
            seccode: result.geetest_seccode,
            account: account,
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