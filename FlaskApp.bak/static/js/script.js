document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('themeToggle');
  const root = document.documentElement;

  // load stored theme
  const theme = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-theme', theme);
  setBtnIcon(theme);

  btn.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', current);
    localStorage.setItem('theme', current);
    setBtnIcon(current);
  });

  function setBtnIcon(theme){
    btn.innerHTML = theme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
  }

  // Fill example values
  const fillBtn = document.getElementById('fillExample');
  const clearBtn = document.getElementById('clearForm');
  if(fillBtn){
    fillBtn.addEventListener('click', () => {
      // collect placeholders and fill inputs
      document.querySelectorAll('#predictForm input[type="text"]').forEach((el) => {
        el.value = el.placeholder;
        el.classList.add('filled');
      });
      document.querySelector('#predictForm textarea').value = '';
    });
  }
  if(clearBtn){
    clearBtn.addEventListener('click', () => {
      document.querySelectorAll('#predictForm input[type="text"]').forEach((el) => el.value = '');
      document.querySelector('#predictForm textarea').value = '';
    });
  }

  // simple animation on form submit
  const form = document.getElementById('predictForm');
  if(form){
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      btn.classList.add('disabled');
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Predicting...';
    });
  }
});
