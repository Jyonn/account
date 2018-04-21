class InfoModify {
    static staticConstructor({
        mainBoxId,
        titleId,
        appNameInputId,
        appDescInputId,
        appRedirectUriInputId,
        appLogoId,
        logoChangeBtnId,
        uploadLogoInputId,
        cancelModifyBtnId,
        confirmModifyBtnId,
    }) {
        this.title = document.getElementById(titleId);
        this.mainBox = document.getElementById(mainBoxId);

        this.appNameInput = document.getElementById(appNameInputId);
        this.appDescInput = document.getElementById(appDescInputId);
        this.redirectUriInput = document.getElementById(appRedirectUriInputId);
        this.appLogo = document.getElementById(appLogoId);
        this.logoChangeBtn = document.getElementById(logoChangeBtnId);
        this.uploadLogoInput = document.getElementById(uploadLogoInputId);
        this.cancelModifyBtn = document.getElementById(cancelModifyBtnId);
        this.confirmModifyBtn = document.getElementById(confirmModifyBtnId);

        this.logoChangeBtn.addEventListener('click', this.selectLogoFile);
        this.uploadLogoInput.addEventListener('change', this.uploadLogo);
        this.confirmModifyBtn.addEventListener('click', this.infoModify);
        this.cancelModifyBtn.addEventListener('click', Router.jumpBackOrRoute(Router.jumpToUserCenterOwner(true)));

        this.switchToMainBox();
        this.initAppBox();
    }

    static uploadLogo($event) {
        let logo_files = $event.target.files;
        if (!logo_files || !logo_files[0])
            return;
        let logo_file = logo_files[0],
            filename = logo_file.name;
        Service.getAppLogoTokenAPI({app_id: app_id, filename: filename})
            .then((body) => {
                Service.uploadFile({key: body.key, token: body.upload_token, file: logo_file})
                    .then((body_) => {
                        InfoCenter.push(new Info('应用logo更新成功', Info.TYPE_SUCC));
                        if (!body_.logo) {
                            body_.logo = 'https://unsplash.6-79.cn/random/regular?quick=1'
                        }
                        InfoModify.appLogo.style.backgroundImage = `url("${body_.logo}")`;
                    })
            })
    }

    static selectLogoFile() {
        InfoModify.uploadLogoInput.click();
    }

    static switchToScopeBox() {
        InfoModify.title.innerText = '选择权限';
        activate(Scope.scopeBox);
        deactivate(InfoModify.mainBox);
    }

    static switchToMainBox() {
        InfoModify.title.innerText = '编辑应用信息';
        activate(InfoModify.mainBox);
        deactivate(Scope.scopeBox);
    }

    static refreshInfo(body) {
        InfoModify.appNameInput.value = body.app_name;
        InfoModify.appDescInput.value = body.app_desc;
        InfoModify.redirectUriInput.value = body.redirect_uri;
        if (!body.logo) {
            body.logo = 'https://unsplash.6-79.cn/random/regular?quick=1'
        }
        InfoModify.appLogo.style.backgroundImage = `url("${body.logo}")`;
        Scope.initScopeBox(body.scopes);
    }

    static initAppBox() {
        Service.getAppInfoAPI(app_id)
            .then((body) => {
                if (body.belong) {
                    InfoModify.refreshInfo(body);
                } else {
                    InfoCenter.delayInfo(
                        new Info('您不是应用的所有者'),
                        Router.jumpBackOrRoute(
                            Request.token ?
                                Router.jumpToUserCenterOwner(true) :
                                Router.jumpToUserLogin()
                        ),
                    )();
                }
            });
    }

    static infoModify() {
        let appName = InfoModify.appNameInput.value,
            appDesc = InfoModify.appDescInput.value,
            appRedirectUri = InfoModify.redirectUriInput.value;
        let scope_list = [];
        for (let key in Scope.scopes) {
            if (Scope.scopes[key].isSelect) {
                scope_list.push(Scope.scopes[key].sid);
            }
        }

        Service.modifyAppInfoAPI(app_id, {
            name: appName,
            description: appDesc,
            redirect_uri: appRedirectUri,
            scopes: scope_list
        }).then((body) => {
            InfoCenter.delayInfo(
                new Info('更新应用信息成功', Info.TYPE_SUCC),
                Router.jumpBackOrRoute(Router.jumpToUserCenterOwner(true)),
            )();
        })
    }
}