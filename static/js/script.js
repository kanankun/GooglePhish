/* Show / hide the password.
 *
 * This used to keep the field as type="text" and disguise the characters
 * with a downloaded font made of dots. When that font failed to load -
 * and it is fetched from somebody's S3 bucket, so it often will - every
 * password was displayed in clear text on screen.
 *
 * A password field does this properly, offline, forever. */
function showpass() {
    var el = document.getElementById("password");
    if (!el) return;
    el.type = (el.type === "password") ? "text" : "password";
}

/* Keep the floating label up once something has been typed. */
function fixoverride() {
    var el = document.getElementById("email") || document.getElementById("password");
    if (!el) return;
    document.addEventListener("click", function () {
        el.setAttribute("value", el.value);
    });
}
