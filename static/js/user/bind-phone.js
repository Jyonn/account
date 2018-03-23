class BindPhone {
    static staticConstructor({
            phoneBoxId,
            regionBoxId,
            footerBoxId,
            switchRegionBtnId,
            regionId,
            backBtnId,
            captchaBoxId,
            titleId,
            captchaInputId,
            nextBtnId,
        }) {
        this.phoneBox = document.getElementById(phoneBoxId);
        this.regionBox = document.getElementById(regionBoxId);
        this.footerBox = document.getElementById(footerBoxId);
        this.switchRegionBtn = document.getElementById(switchRegionBtnId);
        this.region = document.getElementById(regionId);
        this.backBtn = document.getElementById(backBtnId);
        this.nextBtn = document.getElementById(nextBtnId);
        this.captchaBox = document.getElementById(captchaBoxId);
        this.title = document.getElementById(titleId);
        this.captchaInput = document.getElementById(captchaInputId);
        this.switchToPhoneBox();

        this.regionTemplate=template`<div class="region-item" onclick="BindPhone.changeRegion('${0}', '${1}')">${2}</div>`;
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
        BindPhone.title.innerText = '选择国家或地区';
        deactivate(BindPhone.phoneBox);
        deactivate(BindPhone.footerBox);
        deactivate(BindPhone.captchaBox);
        activate(BindPhone.regionBox);
        activate(BindPhone.backBtn);
    }

    static switchToPhoneBox() {
        BindPhone.title.innerText = '绑定手机号';
        activate(BindPhone.phoneBox);
        activate(BindPhone.footerBox);
        deactivate(BindPhone.regionBox);
        deactivate(BindPhone.backBtn);
        deactivate(BindPhone.captchaBox);
    }

    static switchToCaptchaBox() {
        BindPhone.title.innerText = '绑定手机号';
        activate(BindPhone.captchaBox);
        activate(BindPhone.footerBox);
        deactivate(BindPhone.regionBox);
        deactivate(BindPhone.backBtn);
        deactivate(BindPhone.phoneBox);
        // BindPhone.nextBtn.addEventListener('click', BindPhone.BindPhone);
    }

    static changeRegion(regionCode, region) {
        this.region.innerText = '+' + regionCode;
        InfoCenter.push(new Info('切换手机号所在地为'+region, Info.TYPE_SUCC));
        this.switchToPhoneBox();
    }

    // static BindPhone() {
    //     let captcha = BindPhone.captchaInput.value;
    //     let password = BindPhone.passwordInput.value;
    //     Service.BindPhoneAPI({password: password, code: captcha})
    //         .then((body) => {
    //             Request.saveToken(body.token);
    //             InfoCenter.push(new Info('注册成功，正在跳转……', Info.TYPE_SUCC));
    //         })
    // }
}
