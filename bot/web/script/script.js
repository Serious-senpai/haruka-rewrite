function clearChildren(element) {
    element.textContent = "";
}

function initializeMain() {
    var d = document.getElementById("main-inner");
    if (d) {
        clearChildren(d);
        return d;
    }
}

function createHeading(tagName, heading) {
    const h = document.createElement(tagName);
    h.innerHTML = heading;
    return h;
}

function createRandomImage() {
    var img = document.createElement("img");
    img.src = "/collection/random";
    return img;
}

function toImageGenerator() {
    var d = initializeMain();
    if (d) {
        var heading = createHeading("h3", "IMAGE GENERATOR"),
            image = createRandomImage();

        image.alt = "image";
        d.append(heading, image);
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