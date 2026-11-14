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
        // 1. Clic en hamburguesa: cierra el perfil (si estaba abierto) y alterna hamburguesa
        menuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuPerfil();

            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
            menuToggle.setAttribute('aria-expanded', !isExpanded);
            navMenu.style.display = isExpanded ? 'none' : 'flex';
        });

        // 2. Clic en perfil: cierra hamburguesa (si estaba abierto) y alterna perfil
        userMenuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            cerrarMenuHamburguesa();

            const isExpanded = userDropdown.classList.toggle('active');
            userMenuToggle.setAttribute('aria-expanded', isExpanded);
        });

        // 3. Clic afuera: solo revisa el único menú que podría estar abierto
        document.addEventListener('click', (event) => {
            if (navMenu.style.display === 'flex' && !navMenu.contains(event.target)) {
                cerrarMenuHamburguesa();
            } else if (userDropdown.classList.contains('active') && !userDropdown.contains(event.target)) {
                cerrarMenuPerfil();
            }
        });
    }
});