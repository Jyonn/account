class Saying {
    static staticConstructor(sayingId) {
        this.saying = document.getElementById(sayingId);
        this.initSaying();
    }

    static initSaying() {
        Service.getSayingAPI({max_length: 26})
            .then((body) => {
                this.saying.innerText = body.sentence;
            })
    }
}