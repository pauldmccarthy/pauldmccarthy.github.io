// Switch between dark/light page theme
// Thanks https://dev.to/ananyaneogi/create-a-dark-light-mode-switch-with-css-variables-34l8
$(document).ready( function () {

    // unicode sun/moon
    var sun  = "&#9788;";
    var moon = "&#9789;";

    // identify first execution
    var initialised = false;

    // darklight toggle element
    var toggleElem = document.getElementById("darklight-toggle");

    function toggle_darklight_theme() {

        var theme = localStorage.getItem("theme");
        if (!theme) {
            var wantsDark = window.matchMedia("(prefers-color-scheme: dark)");
            if (wantsDark) theme = "dark";
            else           theme = "light";
        }

        // On first load, set to stored theme
        if (!initialised) {
            initialised = true;
        }
        // On clicks, toggle theme
        else {
            if (theme === "dark") theme = "light";
            else                  theme = "dark";
        }

        if (theme == "light") toggleElem.innerHTML = moon;
        else                  toggleElem.innerHTML = sun;

        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    };

    toggleElem.addEventListener("click", toggle_darklight_theme);
    toggle_darklight_theme();
});
