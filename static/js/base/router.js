class Router {
    static abstructJump(location, no_from=false, data={}) {
        return function() {
            if (!no_from) {
                data.from = current_full_path;
            }
            let params = Request.getQueryString(data);
            if (params) {
                location += (location.indexOf('?') === -1) ? '?' : '&';
                location += Request.getQueryString(data);
            }
            window.location.href = location;
        }
    }

    static jumpToApp(uri, {code, state}) {
        return Router.abstructJump(uri, true, arguments[1]);
    }

    static jumpToGithubRepo() {
        return Router.abstructJump(`https://github.com/lqj679ssn/account`, true);
    }

    static jumpToUserCenter(no_from=false) {
        return Router.abstructJump(`/user/center`, no_from, {r: 'user'});
    }

    static jumpToUserInfoModify(no_from=false) {
        return Router.abstructJump(`/user/info-modify`, no_from);
    }

    static jumpToUserSetting(no_from=false) {
        return Router.abstructJump(`/user/settings`, no_from);
    }

    static jumpToUserCenterOwner(no_from=false) {
        return Router.abstructJump(`/user/center`, no_from, {r: 'owner'});
    }

    static jumpToUserLogin(no_from=false) {
        return Router.abstructJump(`/user/login`, no_from);
    }

    static jumpToAppApply(no_from=false) {
        return Router.abstructJump(`/app/apply`, no_from);
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
        if (value) {
            return Router.abstructJump(decodeURIComponent(value), true);
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