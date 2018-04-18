class Center {
    static staticConstructor({
        appBoxUserId,
        appBoxOwnerId,
        switchAppUserBtnId,
        switchAppOwnerBtnId,
    }) {
        this.appBoxAsUser = document.getElementById(appBoxUserId);
        this.appBoxAsOwner = document.getElementById(appBoxOwnerId);

        this.switchAppUserBtn = document.getElementById(switchAppUserBtnId);
        this.switchAppOwnerBtn = document.getElementById(switchAppOwnerBtnId);

        this.appTemplate = template`
            <div class="app-item">
                <div class="main">
                    <div class="full mask"></div>
                    <div class="logo img-fit img-random inactive"></div>
                    <div class="app-name">${0}</div>
                    <div class="description">${1}</div>
                    <div class="btn-box">
                        <span class="remove solid flaticon-trash-can-black-symbol hover-strong" onclick="${2}"></span>
                        <span class="getin solid ${3} hover-strong" onclick="${4}"></span>
                    </div>
                </div>
            </div>
        `;
        this.userSpanClass = 'flaticon-arrow-angle-pointing-to-right';
        this.ownerSpanClass = 'flaticon-keyboard-of-nine-circle-for-digital-devices';

        this.initAppBox();

        let r = Router.getQueryParam('r');
        if (r === 'owner') {
            this.switchToAppOwnerBox();
        } else {
            this.switchToAppUserBox();
        }

        this.switchAppUserBtn.addEventListener('click', this.switchToAppUserBox);
        this.switchAppOwnerBtn.addEventListener('click', this.switchToAppOwnerBox);
    }

    static switchToAppUserBox() {
        activate(Center.appBoxAsUser);
        deactivate(Center.appBoxAsOwner);

        activate(Center.switchAppUserBtn);
        deactivate(Center.switchAppOwnerBtn);
    }

    static switchToAppOwnerBox() {
        deactivate(Center.appBoxAsUser);
        activate(Center.appBoxAsOwner);

        deactivate(Center.switchAppUserBtn);
        activate(Center.switchAppOwnerBtn);
    }

    static initAppBox() {
        Service.getMyAppAPI({relation: 'user'})
            .then((body) => {
                for (let i = 0; i < body.length; i++) {
                    let html = stringToHtml(
                        Center.appTemplate(
                            body[i].app_name,
                            body[i].app_desc,
                            null,
                            Center.userSpanClass,
                            `Router.jumpToOAuth('${body[i].app_id}')`
                        ));
                    this.appBoxAsUser.appendChild(html);
                }
            });
        Service.getMyAppAPI({relation: 'owner'})
            .then((body) => {
                for (let i = 0; i < body.length; i++) {
                    let html = stringToHtml(
                        Center.appTemplate(
                            body[i].app_name,
                            body[i].app_desc,
                            null,
                            Center.ownerSpanClass,
                            `Router.jumpToAppInfoModify('${body[i].app_id}')`
                        ));
                    this.appBoxAsOwner.appendChild(html);
                }
            });
    }
}