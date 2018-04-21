class Router {
    static abstructJump(location, data={}) {
        return function() {
            data.from = current_full_path;
            location += '?' + Request.getQueryString(data);
            window.location.href = location;
        }
    }

    static jumpToUserCenter() {
        return Router.abstructJump(`/user/center`, {r: 'user'});
    }

    static jumpToUserCenterOwner() {
        return Router.abstructJump(`/user/center`, {r: 'owner'});
    }

    static jumpToUserLogin() {
        return Router.abstructJump(`/user/login`);
    }

    static jumpToAppInfoModify(app_id) {
        return Router.abstructJump(`/app/info-modify/${app_id}`);
    }

    static jumpToOAuth(app_id) {
        return Router.abstructJump(`/oauth/?app_id=${app_id}`);
    }

    static jumpToBindPhone() {
        return Router.abstructJump(`/user/bind-phone`);
    }

    static jumpBackOrRoute(router) {
        let value = Router.getQueryParam('from');
        if (value) {
            return Router.abstructJump(value);
        } else if (router) {
            return router;
        }
    }

    static getQueryParam(key) {
        let params = new URLSearchParams(window.location.search);
        if (params.has(key))
            return params.get(key);
    }
}