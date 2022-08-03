function clearChildren(element) {
    element.textContent = "";
}

function initializeMain() {
    var element = document.getElementById("main-inner");
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
    var d = initializeMain();
    if (d) {
        var heading = createHeading("h3", "IMAGE GENERATOR"),
            container = document.createElement("div");

        container.id = "random-image-container";

        var image = document.createElement("img")
        image.id = "random-image";
        image.src = "/collection/random?time=" + Date.now();
        image.alt = "image";
        container.appendChild(image);

        var reloadButton = document.createElement("button")
        reloadButton.id = "reload-button";
        reloadButton.type = "button";
        reloadButton.onclick = toImageGenerator;
        reloadButton.appendChild(materialIcon("refresh"));

        d.append(heading, container, reloadButton);
    }
}

function toPixivUserSearch() {
    var d = initializeMain();
    if (d) {
        const heading = createHeading("h3", "PIXIV USER SEARCH");
        d.appendChild(heading);
        // -- More here --
    }
}