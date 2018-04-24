class OAuth {
    static staticConstructor({
        cancelOAuthId,
        verifyOAuthId,
    }) {
        this.cancelOAuth = document.getElementById(cancelOAuthId);
        this.verifyOAuth = document.getElementById(verifyOAuthId);
        this.appId = Router.getQueryParam('app_id');

        this.cancelOAuth.addEventListener('click',
            InfoCenter.delayInfo(
                new Info('取消授权，正在前往个人主页', Info.TYPE_WARN),
                Router.jumpBackOrRoute(Router.jumpToUserCenter(true)),
                1000,
            ));
        this.verifyOAuth.addEventListener('click', this.oAuthVerify);

        this.getOAuthInfo();
    }

    static getOAuthInfo() {
        Service.getOAuthInfoAPI({app_id: OAuth.appId})
            .then((body) => {
                // Router.jumpToApp(body.redirect_uri, body.auth_code)();
            })
            .catch((err) => console.log(err));
    }

    static oAuthVerify() {
        Service.oAuthAPI({app_id: OAuth.appId})
            .then((body) => {
                InfoCenter.delayInfo(
                    new Info('授权成功，正在前往应用', Info.TYPE_SUCC),
                    Router.jumpToApp(body.redirect_uri, body.auth_code),
                    1000,
                )();
            })
    }
}