class Service {
    static getRegionCodeAPI() {
        return Request.get('/api/base/regions');
    }

    static getSayingAPI({max_length=26}) {
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
}