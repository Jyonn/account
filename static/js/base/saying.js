class Saying {
    static staticConstructor(sayingId) {
        this.saying = document.getElementById(sayingId);
        this.initSaying();
    }

    static initSaying() {
        Service.getSayingAPI({max_length: 24, consider_author: 1})
            .then((body) => {
                this.saying.innerText = `${body.author || '佚名'} | ${body.sentence}`;
            })
    }
}