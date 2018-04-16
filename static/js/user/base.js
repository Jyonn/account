class UserBase {
    static staticConstructor({
        nicknameId,
        descId,
        avatarId,
        successCallback,
        errorCallback,
    }) {
        this.nickname = document.getElementById(nicknameId);
        this.desc = document.getElementById(descId);
        this.avatar = document.getElementById(avatarId);

        this.initMyInfo(successCallback, errorCallback);
    }

    static initMyInfo(successCallback, errorCallback) {
        Service.getMyInfoAPI()
            .then((body) => {
                if (UserBase.nickname) {
                    if (UserBase.nickname.tagName === 'INPUT') {
                        UserBase.nickname.value = body.nickname;
                    } else {
                        UserBase.nickname.innerText = body.nickname || '齐天簿用户';
                    }
                }
                if (UserBase.desc) {
                    if (UserBase.desc.tagName === 'INPUT') {
                        UserBase.desc.value = body.description;
                    } else {
                        UserBase.desc.innerText = body.description || '您还没有填写个性签名';
                    }
                }
                if (UserBase.avatar) {
                    UserBase.avatar.style.backgroundImage = `url('${body.avatar || 'https://unsplash.6-79.cn/random/regular?quick=1'}')`;
                }
                if (successCallback) {
                    successCallback(body);
                }
            })
            .catch(errorCallback);
    }
}