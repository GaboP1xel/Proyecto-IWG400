document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.nav-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userDropdown = document.getElementById('user-dropdown-menu');

    // Elementos del Modal "Acerca de"
    const btnAcercaDe = document.getElementById('btn-acerca-de');
    const modalAcercaDe = document.getElementById('modal-acerca-de');
    const btnCerrarAcercaDe = document.getElementById('btn-cerrar-acerca-de');

    function cerrarMenuHamburguesa() {
        if (menuToggle && navMenu) {
            menuToggle.setAttribute('aria-expanded', 'false');
            navMenu.style.display = 'none';
        }
    }

    function cerrarMenuPerfil() {
        if (userDropdown && userMenuToggle) {
            userDropdown.classList.remove('active');
            userMenuToggle.setAttribute('aria-expanded', 'false');
        }
    }

    function abrirModalAcercaDe() {
        if (modalAcercaDe) {
            modalAcercaDe.classList.add('open');
        }
    }

    function cerrarModalAcercaDe() {
        if (modalAcercaDe) {
            modalAcercaDe.classList.remove('open');
        }
    }

    if (menuToggle && navMenu && userMenuToggle && userDropdown) {
        // 1. Clic en hamburguesa: cierra el perfil y abre la hamburguesa
        menuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuPerfil();

            menuToggle.setAttribute('aria-expanded', 'true');
            navMenu.style.display = 'flex';
        });

        // 2. Clic en avatar: cierra hamburguesa y abre el perfil
        userMenuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuHamburguesa();

            userDropdown.classList.add('active');
            userMenuToggle.setAttribute('aria-expanded', 'true');
        });

        // 3. Clic afuera: cierra cualquiera de los dos menús si está abierto
        document.addEventListener('click', (event) => {
            if (navMenu.style.display === 'flex' && !navMenu.contains(event.target)) {
                cerrarMenuHamburguesa();
            } else if (userDropdown.classList.contains('active') && !userDropdown.contains(event.target)) {
                cerrarMenuPerfil();
            }
        });
    }

    // 4. Lógica del Modal "Acerca de"
    if (btnAcercaDe && modalAcercaDe) {
        btnAcercaDe.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            cerrarMenuHamburguesa();
            abrirModalAcercaDe();
        });

        btnCerrarAcercaDe?.addEventListener('click', cerrarModalAcercaDe);

        // Cerrar al hacer clic en el fondo oscuro (fuera de la tarjeta)
        modalAcercaDe.addEventListener('click', (event) => {
            if (event.target === modalAcercaDe) {
                cerrarModalAcercaDe();
            }
        });

        // Cerrar al presionar la tecla Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modalAcercaDe.classList.contains('open')) {
                cerrarModalAcercaDe();
            }
        });
    }
});