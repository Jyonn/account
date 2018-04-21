class Service {
    static staticConstructor() {
        this.QN_HOST = 'https://up.qiniup.com';
    }

    static getErrorAPI() {
        return Request.get('/api/base/errors');
    }

    static getScopeAPI() {
        return Request.get('/api/app/scope');
    }

    static getRegionCodeAPI() {
        return Request.get('/api/base/regions');
    }

    static getSayingAPI({max_length=26, consider_author=1}) {
        return Request.get('https://saying.6-79.cn/api/sentence/', arguments[0]);
    }

    static verifyCaptchaAPI({challenge, validate, seccode, account, type}) {
        return Request.post('/api/base/captcha', arguments[0]);
    }

    static registerAPI({password, code}) {
        return Request.post('/api/user/', arguments[0]);
    }

    static loginAPI({password}) {
        return Request.post('/api/user/token', arguments[0]);
    }

    static applyAppAPI({name, description, redirect_uri, scopes}) {
        return Request.post('/api/app/', arguments[0]);
    }

    static modifyAppInfoAPI(app_id, {name, description, redirect_uri, scopes}) {
        return Request.put(`/api/app/${app_id}`, arguments[1]);
    }

    static getMyInfoAPI() {
        return Request.get('/api/user/');
    }

    static getMyAppAPI({relation}) {
        return Request.get('/api/app/', arguments[0]);
    }

    static oAuthAPI({app_id}) {
        return Request.post('/api/oauth/', arguments[0]);
    }

    static getAppInfoAPI(app_id) {
        return Request.get(`/api/app/${app_id}`);
    }

    static getAppLogoTokenAPI({app_id, filename}) {
        return Request.get('/api/app/logo', arguments[0]);
    }

    static getUserAvatarTokenAPI({filename}) {
        return Request.get('/api/user/avatar', arguments[0]);
    }

    static uploadFile({key, token, file}) {
        let fd = new FormData();
        fd.append('key', key);
        fd.append('token', token);
        fd.append('file', file);
        return Request.post(Service.QN_HOST, fd, false, false);
    }

    static modifyUserPasswordAPI({password, old_password}) {
        return Request.put('/api/user/', arguments[0]);
    }

    static modifyUserInfoAPI({nickname, description}) {
        return Request.put('/api/user/', arguments[0]);
    }
}

Service.staticConstructor();