document.getElementById('loginForm').addEventListener('submit', function (event) {

    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${username}&password=${password}`
    }).then(response => response.text())
        .then(data => alert(data));
});


document.getElementById('registerForm').addEventListener('submit', function (event) {

    event.preventDefault();

    const username = document.getElementById('reg_username').value;
    const password = document.getElementById('reg_password').value;

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${username}&password=${password}`
    }).then(response => response.text())
        .then(data => alert(data));
});