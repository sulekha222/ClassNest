/* =========================================
   CLASSNEST - JAVASCRIPT
   ========================================= */


// =========================================
// PAGE LOADED
// =========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("ClassNest loaded successfully!");

    // Automatically remove flash messages
    // after a few seconds
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.transition = "opacity 0.5s ease";
            alert.style.opacity = "0";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 4000);

    });

});


// =========================================
// COPY TEXT
// =========================================

function copyText(text) {

    navigator.clipboard.writeText(text)
        .then(function () {

            showMessage("Copied successfully!");

        })
        .catch(function () {

            showMessage("Unable to copy.");

        });

}


// =========================================
// COPY CLASS CODE
// =========================================

function copyClassCode(code) {

    navigator.clipboard.writeText(code)
        .then(function () {

            showMessage("Class code copied: " + code);

        })
        .catch(function () {

            alert("Class code: " + code);

        });

}


// =========================================
// SHOW MESSAGE
// =========================================

function showMessage(message) {

    const messageBox = document.createElement("div");

    messageBox.className = "classnest-toast";

    messageBox.innerHTML = `
        <i class="bi bi-check-circle-fill"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(messageBox);


    setTimeout(function () {

        messageBox.classList.add("show");

    }, 10);


    setTimeout(function () {

        messageBox.classList.remove("show");

        setTimeout(function () {
            messageBox.remove();
        }, 300);

    }, 2500);

}


// =========================================
// PASSWORD VISIBILITY
// =========================================

function togglePassword(inputId, button) {

    const input = document.getElementById(inputId);

    if (!input) {
        return;
    }

    const icon = button.querySelector("i");


    if (input.type === "password") {

        input.type = "text";

        if (icon) {
            icon.classList.remove("bi-eye");
            icon.classList.add("bi-eye-slash");
        }

    } else {

        input.type = "password";

        if (icon) {
            icon.classList.remove("bi-eye-slash");
            icon.classList.add("bi-eye");
        }

    }

}


// =========================================
// CLASSROOM TABS
// =========================================

function showClassTab(tabName, button) {

    const sections = document.querySelectorAll(
        ".classroom-tab-content"
    );

    sections.forEach(function (section) {
        section.classList.remove("active");
    });


    const buttons = document.querySelectorAll(
        ".classroom-tab"
    );

    buttons.forEach(function (btn) {
        btn.classList.remove("active");
    });


    const selectedSection = document.getElementById(tabName);

    if (selectedSection) {
        selectedSection.classList.add("active");
    }


    if (button) {
        button.classList.add("active");
    }

}


// =========================================
// CONFIRM ACTION
// =========================================

function confirmAction(message) {

    return confirm(
        message || "Are you sure you want to continue?"
    );

}


// =========================================
// FILE NAME DISPLAY
// =========================================

function showFileName(input) {

    if (!input || !input.files.length) {
        return;
    }

    const file = input.files[0];

    const fileNameElement =
        document.getElementById("selected-file-name");

    if (fileNameElement) {

        fileNameElement.textContent =
            "Selected file: " + file.name;

    }

}


// =========================================
// DARK MODE
// =========================================

function toggleDarkMode() {

    document.body.classList.toggle("dark-mode");

    const darkModeEnabled =
        document.body.classList.contains("dark-mode");

    localStorage.setItem(
        "classnest-dark-mode",
        darkModeEnabled ? "enabled" : "disabled"
    );

}


// =========================================
// LOAD DARK MODE SETTING
// =========================================

document.addEventListener("DOMContentLoaded", function () {

    const darkMode =
        localStorage.getItem("classnest-dark-mode");

    if (darkMode === "enabled") {

        document.body.classList.add("dark-mode");

    }

});