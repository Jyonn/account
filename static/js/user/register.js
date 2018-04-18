class Register {
    static staticConstructor({
            phoneBoxId,
            regionBoxId,
            footerBoxId,
            switchRegionBtnId,
            regionId,
            backBtnId,
            passwordBoxId,
            titleId,
            captchaInputId,
            passwordInputId,
            nextBtnId,
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
        this.captchaInput = document.getElementById(captchaInputId);
        this.passwordInput = document.getElementById(passwordInputId);
        this.switchToPhoneBox();

        this.regionTemplate=template`<div class="region-item" onclick="Register.changeRegion('${0}', '${1}')">${2}</div>`;
        this.initRegionBox();
        this.switchRegionBtn.addEventListener('click', this.switchToRegionBox);
        this.backBtn.addEventListener('click', this.switchToPhoneBox);
    }

    static initRegionBox() {
        Service.getRegionCodeAPI()
            .then((body) => {
                for (let i = 0; i < body.length; i++) {
                    let html = stringToHtml(
                        this.regionTemplate(
                            body[i].num, body[i].name, body[i].name + ' +' + body[i].num));
                    this.regionBox.appendChild(html);
                }
            });
    }

    static switchToRegionBox() {
        Register.title.innerText = '选择国家或地区';
        deactivate(Register.phoneBox);
        deactivate(Register.footerBox);
        deactivate(Register.captchaBox);
        activate(Register.regionBox);
        activate(Register.backBtn);
    }

    static switchToPhoneBox() {
        Register.title.innerText = '注册齐天簿';
        activate(Register.phoneBox);
        activate(Register.footerBox);
        deactivate(Register.regionBox);
        deactivate(Register.backBtn);
        deactivate(Register.captchaBox);
    }

    static switchToCaptchaBox() {
        Register.title.innerText = '手机号注册';
        activate(Register.captchaBox);
        activate(Register.footerBox);
        deactivate(Register.regionBox);
        deactivate(Register.backBtn);
        deactivate(Register.phoneBox);
        Register.nextBtn.addEventListener('click', Register.register);
    }

    static changeRegion(regionCode, region) {
        this.region.innerText = '+' + regionCode;
        InfoCenter.push(new Info('切换手机号所在地为'+region, Info.TYPE_SUCC));
        this.switchToPhoneBox();
    }

    static register() {
        let captcha = Register.captchaInput.value;
        let password = Register.passwordInput.value;
        Service.registerAPI({password: password, code: captcha})
            .then((body) => {
                Request.saveToken(body.token);
                InfoCenter.delayInfo(
                    new Info('注册成功，正在跳转……', Info.TYPE_SUCC),
                    Router.jumpBackOrRoute(Router.jumpToUserCenter),
                )();
            })
    }
}
