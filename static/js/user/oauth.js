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
                Router.jumpBackOrRoute(Router.jumpToUserCenter()),
            ));
        this.verifyOAuth.addEventListener('click', this.oAuthVerify);
    }

    static oAuthVerify() {
        Service.oAuthAPI({app_id: OAuth.appId})
            .then((body) => {
                InfoCenter.delayInfo(
                    new Info('授权成功，正在前往应用', Info.TYPE_SUCC),
                    // Router.packAbstructJump(`${body.redirect_uri}?code=${body.auth_code}`)
                    function () {
                        console.log(`${body.redirect_uri}?code=${body.auth_code}`);
                    }
                )();
            })
    }
}