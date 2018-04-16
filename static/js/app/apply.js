class Apply {
    static staticConstructor({
            mainBoxId,
            titleId,
            appNameInputId,
            appDescInputId,
            appRedirectUriInputId,
    }) {
        this.title = document.getElementById(titleId);
        this.mainBox = document.getElementById(mainBoxId);

        this.appNameInput = document.getElementById(appNameInputId);
        this.appDescInput = document.getElementById(appDescInputId);
        this.appRedirectUriInput = document.getElementById(appRedirectUriInputId);

        this.switchToMainBox();
        Scope.initScopeBox();
    }

    static switchToScopeBox() {
        Apply.title.innerText = '选择权限';
        activate(Scope.scopeBox);
        deactivate(Apply.mainBox);
    }

    static switchToMainBox() {
        Apply.title.innerText = '申请应用';
        activate(Apply.mainBox);
        deactivate(Scope.scopeBox);
    }

    static apply() {
        let appName = Apply.appNameInput.value;
        let appDesc = Apply.appDescInput.value;
        let appRedirectUri = Apply.appRedirectUriInput.value;
        let scope_list = [];
        for (let key in Scope.scopes) {
            if (Scope.scopes[key].isSelect) {
                scope_list.push(Scope.scopes[key].sid);
            }
        }
        Service.applyAppAPI({
            name: appName,
            description: appDesc,
            redirect_uri: appRedirectUri,
            scopes: scope_list,
        }).then((resp) => {
                console.log(resp);
        })
    }
}