document.addEventListener('DOMContentLoaded', () => {
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const mobileSignUpButton = document.getElementById('mobileSignUp');
    const mobileSignInButton = document.getElementById('mobileSignIn');
    const container = document.getElementById('auth-container');

    function showSignUpPanel() {
        if (!container) return;
        container.classList.add('right-panel-active');
        history.pushState(null, '', '?panel=signup');
    }

    function showSignInPanel() {
        if (!container) return;
        container.classList.remove('right-panel-active');
        history.pushState(null, '', '?panel=login');
    }

    if (signUpButton && container) {
        signUpButton.addEventListener('click', showSignUpPanel);
    }
    if (signInButton && container) {
        signInButton.addEventListener('click', showSignInPanel);
    }
    if (mobileSignUpButton && container) {
        mobileSignUpButton.addEventListener('click', showSignUpPanel);
    }
    if (mobileSignInButton && container) {
        mobileSignInButton.addEventListener('click', showSignInPanel);
    }

    // Handle initial state from URL
    const urlParams = new URLSearchParams(window.location.search);
    if (container && urlParams.get('panel') === 'signup') {
        container.classList.add('right-panel-active');
    }
});
