/**
 * NeuralDesk — app.js
 * Main SPA controller: routing, init, global state
 */

const App = (() => {

  function init() {
    // Init all modules
    Config.init().then(() => {
      Models.init();
      Chat.init();
      Files.init();
      Monitor.init();
    });

    // Init Lucide icons
    if (window.lucide) lucide.createIcons();
  }

  function switchView(name) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.view === name);
    });

    // Update view
    document.querySelectorAll('.view').forEach(el => {
      el.classList.toggle('active', el.id === 'view-' + name);
    });
  }

  function openModelPicker() {
    switchView('models');
  }

  return { init, switchView, openModelPicker };
})();

window.App = App;

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
