function clearChildren(element) {
    element.textContent = "";
}

function initializeMain() {
    const element = document.getElementById("main-inner");
    if (element) {
        clearChildren(element);
        return element;
    }
}

function createHeading(tagName, heading) {
    const element = document.createElement(tagName);
    element.innerHTML = heading;
    return element;
}

function materialIcon(name) {
    const element = document.createElement("span");
    element.innerHTML = name;
    element.className = "material-icons";
    return element;
}

function toImageGenerator() {
    const d = initializeMain();
    if (d) {
        const heading = createHeading("h3", "IMAGE GENERATOR"),
            container = document.createElement("div");

        container.id = "random-image-container";

        const image = document.createElement("img")
        image.id = "random-image";
        image.src = "/collection/random?time=" + Date.now();
        image.alt = "image";
        container.appendChild(image);

        const reloadButton = document.createElement("button")
        reloadButton.id = "reload-button";
        reloadButton.type = "button";
        reloadButton.onclick = toImageGenerator;
        reloadButton.appendChild(materialIcon("refresh"));

        d.append(heading, container, reloadButton);
    }
}

function toPixivUserSearch() {
    const d = initializeMain();
    if (d) {
        const heading = createHeading("h3", "PIXIV USER SEARCH"),
            form = document.createElement("form");

        form.id = "user-url-form";
        form.action = "/pixiv-user";

        const input = document.createElement("input");
        input.id = "user-url-input";
        input.type = "text";
        input.name = "url";
        input.autocomplete = false;
        input.placeholder = "Pixiv artist URL";

        const submit = document.createElement("input");
        submit.id = "user-url-submit";
        submit.type = "submit";
        submit.value = "Download all artworks";

        form.append(input, submit);

        d.append(heading, form);
    }
}