class Scope {
    static staticConstructor({
        scopeBoxId,
        scopeSectionId,
        scopeTextId,
    }) {
        this.scopeSection = document.getElementById(scopeSectionId);
        this.scopeBox = document.getElementById(scopeBoxId);
        this.scopeText = document.getElementById(scopeTextId);
    }

    static refreshScopeText() {
        let counter = 0, finalText;
        for (let key in Scope.scopes) {
            if (Scope.scopes[key].isSelect) {
                counter += 1;
                finalText = Scope.scopes[key].desc;
            }
        }
        if (counter) {
            finalText += `等 ${counter}项权限…`;
        } else {
            finalText = '选择权限…';
        }
        Scope.scopeText.innerText = finalText;
    }

    static initScopeBox(appScopes=[]) {
        Scope.scopeTemplate = template`
            <div class="item select" onclick="Scope.revertScope(this, ${0})">
                <div class="full mask"></div>
                <div class="text">${1}</div>
                <span class="select ${2}"></span>
            </div>`;
        Scope.scopeSelectedClasses = ['selected', 'solid', 'flaticon-verify-circular-black-button-symbol'];
        Scope.scopeUnselectedClasses = ['unselected', 'line', 'flaticon-minus-circular-button'];
        Service.getScopeAPI()
            .then((body) => {
                Scope.scopes = {};
                for (let i = 0; i < body.length; i++) {
                    let cls;
                    body[i].isSelect = body[i].always || false;
                    if (body[i].isSelect) {
                        cls = Scope.scopeSelectedClasses;
                    } else {
                        cls = Scope.scopeUnselectedClasses;
                    }
                    let html = stringToHtml(
                            Scope.scopeTemplate(
                                body[i].sid, body[i].desc, cls.join(' ')));
                    Scope.scopeSection.appendChild(html);
                    Scope.scopes[body[i].sid] = body[i];
                }
                for (let i = 0; i < appScopes.length; i++) {
                    Scope.scopes[appScopes[i].sid].isSelect = true;
                }
                Scope.refreshScopeText();
            })
    }

    static revertScope(item, sid) {
        let addClasses, removeClasses;
        let scope = Scope.scopes[sid];
        if (scope.always === true) {
            return InfoCenter.push(new Info('应用默认可以获得此权限', Info.TYPE_SUCC));
        }
        if (scope.always === false) {
            return InfoCenter.push(new Info('暂时不允许应用获得此权限'));
        }
        scope.isSelect = !scope.isSelect;
        if (scope.isSelect) {
            addClasses = Scope.scopeSelectedClasses;
            removeClasses = Scope.scopeUnselectedClasses;
        } else {
            addClasses = Scope.scopeUnselectedClasses;
            removeClasses = Scope.scopeSelectedClasses;
        }
        let span = item.getElementsByTagName('span')[0];
        for (let i = 0; i < removeClasses.length; i++) {
            span.classList.remove(removeClasses[i]);
        }
        for (let i = 0; i < addClasses.length; i++) {
            span.classList.add(addClasses[i]);
        }
        Scope.refreshScopeText();
    }
}