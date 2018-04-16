class Router {
    static abstructJump(location) {
        window.location.href = location;
    }

    static packAbstructJump(location) {
        return function () {
            Router.abstructJump(location);
        }
    }

    static jumpToUserCenter() {
        Router.abstructJump('/user/center');
    }

    static jumpToUserLogin() {
        Router.abstructJump('/user/login');
    }

    static jumpBackOrRoute(router) {
        return function () {
            let value = Router.getQueryParam('from');
            if (value) {
                Router.abstructJump(value);
            } else if (router) {
                router();
            }
        }
    }

    static getQueryParam(key) {
        let params = new URLSearchParams(window.location.search);
        if (params.has(key))
            return params.get(key);
    }
}