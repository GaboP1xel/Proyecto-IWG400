document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.nav-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userDropdown = document.getElementById('user-dropdown-menu');

    function cerrarMenuHamburguesa() {
        menuToggle.setAttribute('aria-expanded', 'false');
        navMenu.style.display = 'none';
    }

    function cerrarMenuPerfil() {
        userDropdown.classList.remove('active');
        userMenuToggle.setAttribute('aria-expanded', 'false');
    }

    if (menuToggle && navMenu && userMenuToggle && userDropdown) {
        // 1. Clic en hamburguesa: cierra el perfil y SOLO abre la hamburguesa
        menuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuPerfil();

            menuToggle.setAttribute('aria-expanded', 'true');
            navMenu.style.display = 'flex';
        });

        // 2. Clic en avatar: cierra hamburguesa y SOLO abre el perfil
        userMenuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuHamburguesa();

            userDropdown.classList.add('active');
            userMenuToggle.setAttribute('aria-expanded', 'true');
        });

        // 3. Clic afuera: sigue cerrando cualquiera de los dos si haces clic fuera
        document.addEventListener('click', (event) => {
            if (navMenu.style.display === 'flex' && !navMenu.contains(event.target)) {
                cerrarMenuHamburguesa();
            } else if (userDropdown.classList.contains('active') && !userDropdown.contains(event.target)) {
                cerrarMenuPerfil();
            }
        });
    }
});