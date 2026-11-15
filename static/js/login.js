document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA DE PESTAÑAS Y SINCRONIZACIÓN DE URL ---
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');

    function switchTab(showLogin, updateUrl = true) {
        if (showLogin) {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            formLogin.classList.add('active-form');
            formRegister.classList.remove('active-form');

            if (updateUrl && window.location.pathname !== '/login/') {
                window.history.pushState({ tab: 'login' }, '', '/login/');
            }
        } else {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            formRegister.classList.add('active-form');
            formLogin.classList.remove('active-form');

            if (updateUrl && window.location.pathname !== '/login/registro/') {
                window.history.pushState({ tab: 'registro' }, '', '/login/registro/');
            }
        }
    }

    // Si entra directo o recarga en /login/registro/, abre la pestaña de registro
    if (window.location.pathname.includes('/registro')) {
        switchTab(false, false);
    }

    tabLogin.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab(true, true);
    });

    tabRegister.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab(false, true);
    });

    // Sincroniza al usar los botones Atrás/Adelante del navegador
    window.addEventListener('popstate', () => {
        switchTab(!window.location.pathname.includes('/registro'), false);
    });

    // --- LÓGICA DE VALIDACIÓN (CIBERSEGURIDAD) ---
    const regUser = document.getElementById('reg-user');
    const regPass = document.getElementById('reg-pass');
    const regPass2 = document.getElementById('reg-pass2');
    const btnRegister = document.getElementById('btn-register');
    const errUser = document.getElementById('err-user');
    const errPass2 = document.getElementById('err-pass2');

    const reqLen = document.getElementById('req-len');
    const reqUp = document.getElementById('req-up');
    const reqLow = document.getElementById('req-low');
    const reqNum = document.getElementById('req-num');
    const reqSpc = document.getElementById('req-spc');

    const passPatterns = {
        length: /.{8,}/,
        up: /[A-Z]/,
        low: /[a-z]/,
        num: /[0-9]/,
        spc: /[@$!%*?&]/
    };

    let isUserValid = false;
    let isPassValid = false;
    let isPassMatch = false;

    regUser.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        const isValid = /^[a-zA-Z0-9]{4,20}$/.test(val);

        if (val.length > 0 && !isValid) {
            errUser.textContent = 'Mínimo 4 caracteres. Sin espacios ni símbolos.';
            isUserValid = false;
        } else {
            errUser.textContent = '';
            isUserValid = isValid;
        }
        checkFormReady();
    });

    regPass.addEventListener('input', (e) => {
        const val = e.target.value;

        const validations = {
            length: passPatterns.length.test(val),
            up: passPatterns.up.test(val),
            low: passPatterns.low.test(val),
            num: passPatterns.num.test(val),
            spc: passPatterns.spc.test(val)
        };

        updateReqNode(reqLen, validations.length);
        updateReqNode(reqUp, validations.up);
        updateReqNode(reqLow, validations.low);
        updateReqNode(reqNum, validations.num);
        updateReqNode(reqSpc, validations.spc);

        isPassValid = Object.values(validations).every(v => v === true);

        checkPassMatch();
        checkFormReady();
    });

    regPass2.addEventListener('input', () => {
        checkPassMatch();
        checkFormReady();
    });

    function updateReqNode(node, isValid) {
        if (isValid) {
            node.classList.remove('invalid');
            node.classList.add('valid');
        } else {
            node.classList.remove('valid');
            node.classList.add('invalid');
        }
    }

    function checkPassMatch() {
        if (regPass2.value.length > 0) {
            if (regPass.value !== regPass2.value) {
                errPass2.textContent = 'Las contraseñas no coinciden.';
                isPassMatch = false;
            } else {
                errPass2.textContent = '';
                isPassMatch = true;
            }
        } else {
            errPass2.textContent = '';
            isPassMatch = false;
        }
    }

    function checkFormReady() {
        btnRegister.disabled = !(isUserValid && isPassValid && isPassMatch);
    }
});