document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA DE PESTAÑAS (TABS) ---
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');

    function switchTab(showLogin) {
        if (showLogin) {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            formLogin.classList.add('active-form');
            formRegister.classList.remove('active-form');
        } else {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            formRegister.classList.add('active-form');
            formLogin.classList.remove('active-form');
        }
    }

    tabLogin.addEventListener('click', (e) => { e.preventDefault(); switchTab(true); });
    tabRegister.addEventListener('click', (e) => { e.preventDefault(); switchTab(false); });

    // --- LÓGICA DE VALIDACIÓN (CIBERSEGURIDAD) ---
    const regUser = document.getElementById('reg-user');
    const regPass = document.getElementById('reg-pass');
    const regPass2 = document.getElementById('reg-pass2');
    const btnRegister = document.getElementById('btn-register');
    const errUser = document.getElementById('err-user');
    const errPass2 = document.getElementById('err-pass2');

    // Nodos de requisitos de contraseña
    const reqLen = document.getElementById('req-len');
    const reqUp = document.getElementById('req-up');
    const reqLow = document.getElementById('req-low');
    const reqNum = document.getElementById('req-num');
    const reqSpc = document.getElementById('req-spc');

    // Patrones de ciberseguridad
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

    // 1. Validar Usuario (Mínimo 4 caracteres, alfanumérico)
    regUser.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        // Regex: Letras y números, 4 a 20 caracteres
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

    // 2. Validar Fuerza de Contraseña (Requisitos modernos)
    regPass.addEventListener('input', (e) => {
        const val = e.target.value;
        
        const validations = {
            length: passPatterns.length.test(val),
            up: passPatterns.up.test(val),
            low: passPatterns.low.test(val),
            num: passPatterns.num.test(val),
            spc: passPatterns.spc.test(val)
        };

        // Actualizar UI
        updateReqNode(reqLen, validations.length);
        updateReqNode(reqUp, validations.up);
        updateReqNode(reqLow, validations.low);
        updateReqNode(reqNum, validations.num);
        updateReqNode(reqSpc, validations.spc);

        // Validar si todos los requisitos se cumplen
        isPassValid = Object.values(validations).every(v => v === true);
        
        // Re-verificar coincidencia si ya habían escrito algo abajo
        checkPassMatch();
        checkFormReady();
    });

    // 3. Validar Confirmación de Contraseña
    regPass2.addEventListener('input', () => {
        checkPassMatch();
        checkFormReady();
    });

    // Función auxiliar para actualizar los colores del listado
    function updateReqNode(node, isValid) {
        if (isValid) {
            node.classList.remove('invalid');
            node.classList.add('valid');
        } else {
            node.classList.remove('valid');
            node.classList.add('invalid');
        }
    }

    // Función auxiliar para revisar igualdad de contraseñas
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

    // Activar/Desactivar botón final
    function checkFormReady() {
        if (isUserValid && isPassValid && isPassMatch) {
            btnRegister.disabled = false;
        } else {
            btnRegister.disabled = true;
        }
    }
});
