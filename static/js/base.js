let active = 'active';
let inactive = 'inactive';

function activate(ele) {
    ele.classList.add(active);
    ele.classList.remove(inactive);
}

function deactivate(ele) {
    ele.classList.add(inactive);
    ele.classList.remove(active);
}

class Method {
    static staticConstructor() {
        this.GET = 'get';
        this.POST = 'post';
        this.PUT = 'put';
        this.DELETE = 'delete';
        this.PATCH = 'patch';
    }
}

class ErrorHandler {
    static handler(error) {
        return Promise.reject(error);
    }
}

class Request {
    static staticConstructor() {
        this.token = window.localStorage.getItem('token');
        if (this.token) {
            Request.get('/api/user/')
                .then((resp) => {
                    Request.user = new User(resp);
                })
        }
    }
    static saveToken(token) {
        this.token = token;
        window.localStorage.setItem('token', token);
    }
    static getQueryString(params) {
      const esc = encodeURIComponent;
      return Object.keys(params)
        .map(k => esc(k) + '=' + esc(params[k]))
        .join('&');
    }
    static async baseFetch(method, url, data=null) {
        if ((method === Method.GET || method === Method.DELETE) && data) {
            url += '?' + this.getQueryString(data);
            data = null;
        }
        let req = await fetch(url, {
            method: method,
            headers: {
                "Content-type": "application/json",
                "Token": this.token || '',
            },
            body: data ? JSON.stringify(data) : null,
            credentials: "include",
        });
        return req.json().then((resp) => {
            if (resp.code !== 0) {
                InfoCenter.push(new Info(resp.msg));
                return ErrorHandler.handler(resp);
            }
            return resp.body;
        }).catch(ErrorHandler.handler);
    }
    static async get(url, data=null) {
        return this.baseFetch(Method.GET, url, data);
    }
    static async post(url, data=null) {
        return this.baseFetch(Method.POST, url, data);
    }
    static async put(url, data=null) {
        return this.baseFetch(Method.PUT, url, data);
    }
    static async delete(url, data=null) {
        return this.baseFetch(Method.DELETE, url, data);
    }
}

// new Request().get('/api/user/@root');

function get_random_string() {
    return Math.random().toString(36).substr(2, 5);
}

function template(strings, ...keys) {
    return (function (...values) {
        const dict = values[values.length - 1] || {};
        const result = [strings[0]];
        keys.forEach(function (key, i) {
            const value = Number.isInteger(key) ? values[key] : dict[key];
            result.push(value, strings[i + 1]);
        });
        return result.join('');
    });
}

function stringToHtml(s) {
    let tmp = document.createElement('div');
    tmp.innerHTML = s;
    return tmp.firstElementChild;
}

Method.staticConstructor();
Request.staticConstructor();