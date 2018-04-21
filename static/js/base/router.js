class Router {
    static abstructJump(location, data={}, no_from=false) {
        return function() {
            if (!no_from) {
                data.from = current_full_path;
            }
            if (data) {
                location += '?' + Request.getQueryString(data);
            }
            window.location.href = location;
        }
    }

    static jumpToUserCenter(no_from=false) {
        return Router.abstructJump(`/user/center`, {r: 'user'}, no_from);
    }

    static jumpToUserCenterOwner(no_from=false) {
        return Router.abstructJump(`/user/center`, {r: 'owner'}, no_from);
    }

    static jumpToUserLogin(no_from=false) {
        return Router.abstructJump(`/user/login`, no_from);
    }

    // center.js
    static jumpToAppInfoModify(app_id, no_from=false) {
        return Router.abstructJump(`/app/info-modify/${app_id}`, no_from);
    }

    // center.js
    static jumpToOAuth(app_id, no_from=false) {
        return Router.abstructJump(`/oauth/?app_id=${app_id}`, no_from);
    }

    static jumpToBindPhone(no_from=false) {
        return Router.abstructJump(`/user/bind-phone`, no_from);
    }

    static jumpBackOrRoute(router) {
        let value = Router.getQueryParam('from');
        console.log(value);
        if (value) {
            return Router.abstructJump(value, null, true);
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