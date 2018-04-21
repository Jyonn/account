class Login {
    static staticConstructor({
            phoneBoxId,
            regionBoxId,
            footerBoxId,
            switchRegionBtnId,
            regionId,
            backBtnId,
            passwordBoxId,
            titleId,
            passwordInputId,
            nextBtnId,
            phoneItemId,
            qitianItemId,
        }) {
        this.phoneBox = document.getElementById(phoneBoxId);
        this.regionBox = document.getElementById(regionBoxId);
        this.footerBox = document.getElementById(footerBoxId);
        this.switchRegionBtn = document.getElementById(switchRegionBtnId);
        this.region = document.getElementById(regionId);
        this.backBtn = document.getElementById(backBtnId);
        this.nextBtn = document.getElementById(nextBtnId);
        this.captchaBox = document.getElementById(passwordBoxId);
        this.title = document.getElementById(titleId);
        this.passwordInput = document.getElementById(passwordInputId);
        this.phoneItem = document.getElementById(phoneItemId);
        this.qitianItem = document.getElementById(qitianItemId);
        this.loginWithPhone = 'phone';
        this.loginWithQitian = 'qitian';
        this.activatePhoneItem();
        this.switchToPhoneBox();

        this.regionTemplate=template`<div class="region-item" onclick="Login.changeRegion('${0}', '${1}')">${2}</div>`;
        this.initRegionBox();
        this.switchRegionBtn.addEventListener('click', this.switchToRegionBox);
        this.backBtn.addEventListener('click', this.switchToPhoneBox);
    }

    static initRegionBox() {
        Service.getRegionCodeAPI()
            .then((body) => {
                for (let i = 0; i < body.length; i++) {
                    let html = stringToHtml(
                        Login.regionTemplate(
                            body[i].num, body[i].name, body[i].name + ' +' + body[i].num));
                    Login.regionBox.appendChild(html);
                }
            });
    }

    static switchToRegionBox() {
        Login.title.innerText = '选择国家或地区';
        deactivate(Login.phoneBox);
        deactivate(Login.footerBox);
        deactivate(Login.captchaBox);
        activate(Login.regionBox);
        activate(Login.backBtn);
    }

    static switchToPhoneBox() {
        Login.title.innerText = '登录齐天簿';
        activate(Login.phoneBox);
        activate(Login.footerBox);
        deactivate(Login.regionBox);
        deactivate(Login.backBtn);
        deactivate(Login.captchaBox);
    }

    static switchToCaptchaBox() {
        Login.title.innerText = '手机号登录';
        activate(Login.captchaBox);
        activate(Login.footerBox);
        deactivate(Login.regionBox);
        deactivate(Login.backBtn);
        deactivate(Login.phoneBox);
        Login.nextBtn.addEventListener('click', Login.login);
    }

    static changeRegion(regionCode, region) {
        this.region.innerText = '+' + regionCode;
        InfoCenter.push(new Info('切换手机号所在地为'+region, Info.TYPE_SUCC));
        this.switchToPhoneBox();
    }

    static login(succFunc, failFunc) {
        let password = Login.passwordInput.value;
        Service.loginAPI({password: password})
            .then((body) => {
                Request.saveToken(body.token);
                InfoCenter.delayInfo(
                    new Info('登录成功，正在跳转……', Info.TYPE_SUCC),
                    Router.jumpBackOrRoute(Router.jumpToUserCenter(true)),
                )();
            })
            .catch((resp) => {
                if (MyError.check('ERROR_SESSION', resp)) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            });
    }

    static activatePhoneItem() {
        Login.loginType = Login.loginWithPhone;
        activate(Login.phoneItem);
        deactivate(Login.qitianItem);
    }

    static activateQitianItem() {
        Login.loginType = Login.loginWithQitian;
        activate(Login.qitianItem);
        deactivate(Login.phoneItem);
    }
}
