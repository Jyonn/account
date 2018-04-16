class Center {
    static staticConstructor({
        appBoxId,
    }) {
        this.appBox = document.getElementById(appBoxId);

        this.appTemplate = template`
            <div class="app-item">
                <div class="main">
                    <div class="full mask"></div>
                    <div class="logo img-fit img-random inactive"></div>
                    <div class="app-name">${0}</div>
                    <div class="description">${1}</div>
                    <div class="btn-box">
                        <span class="remove solid flaticon-trash-can-black-symbol hover-strong"/>
                        <span class="getin solid flaticon-arrow-angle-pointing-to-right hover-strong"/>
                    </div>
                </div>
            </div>
        `;

        this.initAppBox();
    }

    static initAppBox() {
        Service.getMyAppAPI()
            .then((body) => {
                for (let i = 0; i < body.length; i++) {
                    let html = stringToHtml(
                        Center.appTemplate(
                            body[i].name, body[i].desc));
                    this.appBox.appendChild(html);
                }
            })
    }
}