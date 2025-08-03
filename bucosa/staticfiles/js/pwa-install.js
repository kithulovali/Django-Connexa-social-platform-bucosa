  
      let deferredPrompt;
      const installBtn = document.getElementById('pwa-install-btn');
      function hideInstallBtnIfInstalled() {
        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
          installBtn.style.display = 'none';
        } else {
          installBtn.style.display = 'block';
        }
      }
      hideInstallBtnIfInstalled();
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        hideInstallBtnIfInstalled();
      });
      window.addEventListener('appinstalled', () => {
        installBtn.style.display = 'none';
      });
      installBtn.addEventListener('click', async () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          const { outcome } = await deferredPrompt.userChoice;
          if (outcome === 'accepted') {
            installBtn.style.display = 'none';
          }
          deferredPrompt = null;
        } else {
          alert('PWA install prompt is not available in this browser or context.');
        }
      });
    