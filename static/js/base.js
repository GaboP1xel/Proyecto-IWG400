
document.addEventListener('DOMContentLoaded', () => {
    // Capturamos el botón de hamburguesa y el menú de navegación
    const menuToggle = document.querySelector('.nav-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (menuToggle && navMenu) {
        // Alternar el menú al hacer clic en el botón de hamburguesa
        menuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
            
            menuToggle.setAttribute('aria-expanded', !isExpanded);
            navMenu.style.display = isExpanded ? 'none' : 'flex';
        });

        // Cerrar el menú si se hace clic en cualquier parte fuera de él
        document.addEventListener('click', (event) => {
            if (!navMenu.contains(event.target) && event.target !== menuToggle) {
                menuToggle.setAttribute('aria-expanded', 'false');
                navMenu.style.display = 'none';
            }
        });
    }

    // Capturamos el botón del avatar y el menú desplegable
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userDropdown = document.getElementById('user-dropdown-menu');

    if (userMenuToggle && userDropdown) {
        
        // Alternar (Abrir/Cerrar) al hacer clic en la foto de perfil
        userMenuToggle.addEventListener('click', (event) => {
            event.stopPropagation(); // Evita que el clic se propague y cierre instantáneamente
            userDropdown.classList.toggle('active');
            
            const isExpanded = userDropdown.classList.contains('active');
            userMenuToggle.setAttribute('aria-expanded', isExpanded);
        });

        // Cerrar ventana si el usuario hace clic fuera de ella
        document.addEventListener('click', (event) => {
            if (!userDropdown.contains(event.target) && event.target !== userMenuToggle) {
                userDropdown.classList.remove('active');
                userMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
});