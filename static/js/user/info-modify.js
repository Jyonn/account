class InfoModify {
    static staticConstructor({
        mainBoxId,
        passwordBoxId,
        nicknameInputId,
        descInputId,
        qitianInputId,
        oldPasswordInputId,
        newPasswordInputId,
        cancelModifyBtnId,
        confirmModifyBtnId,
        avatarId,
        uploadAvatarInputId,
    }) {
        this.mainBox = document.getElementById(mainBoxId);
        this.passwordBox = document.getElementById(passwordBoxId);
        this.nicknameInput = document.getElementById(nicknameInputId);
        this.descInput = document.getElementById(descInputId);
        this.qitianInput = document.getElementById(qitianInputId);
        this.oldPassword = document.getElementById(oldPasswordInputId);
        this.newPassword = document.getElementById(newPasswordInputId);
        this.cancelModifyBtn = document.getElementById(cancelModifyBtnId);
        this.confirmModifyBtn = document.getElementById(confirmModifyBtnId);
        this.avatar = document.getElementById(avatarId);
        this.uploadAvatarInput = document.getElementById(uploadAvatarInputId);

        this.avatar.addEventListener('click', this.selectAvatarFile);
        this.uploadAvatarInput.addEventListener('change', this.uploadAvatar);
        this.confirmModifyBtn.addEventListener('click', this.infoModify);
        this.cancelModifyBtn.addEventListener('click', Router.jumpBackOrRoute(Router.jumpToUserCenter(true)));

        this.switchToMainBox();
    }

    static uploadAvatar($event) {
        let avatar_files = $event.target.files;
        if (!avatar_files || !avatar_files[0])
            return;
        let avatar_file = avatar_files[0],
            filename = avatar_file.name;
        Service.getUserAvatarTokenAPI({filename: filename})
            .then((body) => {
                Service.uploadFile({key: body.key, token: body.upload_token, file: avatar_file})
                    .then((body_) => {
                        InfoCenter.push(new Info('用户头像更新成功', Info.TYPE_SUCC));
                        if (!body_.avatar) {
                            body_.avatar = 'https://unsplash.6-79.cn/random/regular?quick=1';
                        }
                        InfoModify.avatar.style.backgroundImage = `url("${body_.avatar}")`;
                    })
            })
    }

    static selectAvatarFile() {
        InfoModify.uploadAvatarInput.click();
    }

    static switchToPasswordBox() {
        activate(InfoModify.passwordBox);
        deactivate(InfoModify.mainBox);
    }

    static switchToMainBox() {
        activate(InfoModify.mainBox);
        deactivate(InfoModify.passwordBox);
    }

    static modifyPassword() {
        let new_password = InfoModify.newPassword.value,
            old_password = InfoModify.oldPassword.value;
        Service.modifyUserPasswordAPI({password: new_password, old_password: old_password})
            .then(InfoCenter.delayInfo(
                    new Info('修改密码成功', Info.TYPE_SUCC),
                    InfoModify.switchToMainBox,
                    1000,
            ));
    }

    static infoModify() {
        let nickname = InfoModify.nicknameInput.value;
        let user_desc = InfoModify.descInput.value;
        let qitian = InfoModify.qitianInput.value;

        Service.modifyUserInfoAPI({
            nickname: nickname,
            description: user_desc,
            qitian: qitian,
        })
            .then((body) => {

            })
    }
}