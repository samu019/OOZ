document.addEventListener('DOMContentLoaded', () => {
  const toggleThemeBtn = document.getElementById('toggleThemeBtn');
  const themeIcon = document.getElementById('themeIcon');

  // Comprobar si el body tiene la clase 'dark-mode' al cargar
  if (document.body.classList.contains('dark-mode')) {
    themeIcon.textContent = '🌑'; // Modo oscuro
  } else {
    themeIcon.textContent = '🌙'; // Modo claro
  }

  // Alternar el tema al presionar el botón
  toggleThemeBtn.addEventListener('click', () => {
    // Alternar entre las clases 'dark-mode' y 'light-mode'
    document.body.classList.toggle('dark-mode');
    document.body.classList.toggle('light-mode');
    
    // Cambiar el icono del botón según el tema
    if (document.body.classList.contains('dark-mode')) {
      themeIcon.textContent = '🌑'; // Modo oscuro
    } else {
      themeIcon.textContent = '🌙'; // Modo claro
    }
  });
});
