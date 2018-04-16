class MyError {
    static staticConstructor() {
        Service.getErrorAPI()
            .then((body) => MyError._dict = body)
    }
    static check(key, resp) {
        return MyError._dict[key].eid === resp.code;
    }
}

MyError.staticConstructor();
