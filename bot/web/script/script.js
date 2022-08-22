/**
 * Initialize body on load 
 * 
 * @return {void}
 */
function initialize_body() {
    const url = new URL(document.location);
    const params = url.searchParams;

    if (params.get("image-generator")) {
        toImageGenerator();
    } else if (params.get("pixiv-user-search")) {
        toPixivUserSearch();
    } else if (params.get("audio-control")) {
        const key = params.get("key");
        if (key) {
            toAudioControl(key);
        }
    }
}


/**
 * Make a HTTP request
 * 
 * @param {string} url The target URL
 * @param {function(XMLHttpRequest):any} callback The callback function to
 * be called when the request is completed. The only argument
 * is the response body.
 * 
 * @return {void}
 */
function getAsync(url, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onload = (e) => callback(e.target);
    xhr.send();
}


/**
 * Create a websocket that automatically reconnects and handles
 * incoming messages
 * 
 * @param {string} url The target URL
 * @param {function(MessageEvent):any} onmessage The websocket message
 * handler
 * @param {function(CloseEvent):any} onclose The websocket closure handler
 * 
 * @return {void}
 */
function wsConnect(url, onmessage, onclose) {
    const websocket = new WebSocket(url);
    websocket.onmessage = onmessage;
    websocket.onclose = onclose;
}


/** 
 * Clear all children of an element
 * @param {HTMLElement} element The element to clear all children
 * 
 * @return {void}
 */
function clearChildren(element) {
    element.textContent = "";
}


/**
 * Initialize the main HTML section
 * 
 * @return {HTMLElement} The main section
 */
function initializeMain() {
    const element = document.getElementById("main-inner");
    if (element) {
        clearChildren(element);
        return element;
    }
}


/**
 * Create a heading element with content
 * 
 * @param {string} tagName The tag name (h1, h2, ...)
 * @param {string} content The content of the heading
 * 
 * @return {HTMLHeadingElement} The created heading element
 */
function createHeading(tagName, content) {
    const element = document.createElement(tagName);
    element.innerHTML = content;
    return element;
}


/**
 * Create an icon from Google Fonts Material
 * Reference: https://fonts.google.com/icons?icon.set=Material+Icons
 * 
 * @param {string} name The icon name
 * 
 * @return {HTMLSpanElement} The element to be injected to HTML
 */
function materialIcon(name) {
    const element = document.createElement("span");
    element.innerHTML = name;
    element.className = "material-icons";
    return element;
}


/**
 * Display the image generator HTML content
 * 
 * @return {void}
 */
function toImageGenerator() {
    const d = initializeMain();
    {
        const heading = createHeading("h3", "IMAGE GENERATOR");

        const container = document.createElement("div");
        container.id = "random-image-container";
        {
            const image = document.createElement("img")
            image.alt = "image";
            image.id = "random-image";
            image.src = "/collection/random?time=" + Date.now();
            container.appendChild(image);
        }

        const reloadButton = document.createElement("button")
        reloadButton.id = "reload-button";
        reloadButton.type = "button";
        reloadButton.onclick = toImageGenerator;
        reloadButton.appendChild(materialIcon("refresh"));

        d.append(heading, container, reloadButton);
    }
}


/**
 * Display the Pixiv user search HTML content
 * 
 * @return {void}
 */
function toPixivUserSearch() {
    const d = initializeMain();
    {
        const heading = createHeading("h3", "PIXIV USER SEARCH");

        const form = document.createElement("form");
        form.action = "/pixiv-user";
        form.id = "user-url-form";
        {
            const input = document.createElement("input");
            input.autocomplete = false;
            input.id = "user-url-input";
            input.name = "url";
            input.placeholder = "Pixiv artist URL";
            input.type = "text";

            const submit = document.createElement("input");
            submit.id = "user-url-submit";
            submit.type = "submit";
            submit.value = "Download all artworks";

            form.append(input, submit);
        }

        d.append(heading, form);
    }
}


/**
 * Display the audio control HTML content
 * 
 * @param {string} key The music client's key, this may be valid or not
 * 
 * @return {void}
 */
function toAudioControl(key) {
    initializeMain();
    getAsync(
        "/audio-control/playing?key=" + key,
        (request) => {
            if (request.status != 200) return;

            const data = JSON.parse(request.responseText);

            const d = initializeMain();
            {
                const thumbnail = document.createElement("img");
                thumbnail.alt = "Track thumbnail";
                thumbnail.id = "track-thumbnail";
                thumbnail.src = data["thumbnail"];

                const title = createHeading("h3", data["title"]);

                const controlButtons = document.createElement("div");
                controlButtons.id = "control-buttons";
                {
                    const pauseButton = document.createElement("a")
                    pauseButton.className = "button";
                    pauseButton.href = "/pause?key=" + key;
                    pauseButton.appendChild(materialIcon("pause"));

                    const resumeButton = document.createElement("a")
                    resumeButton.className = "button";
                    resumeButton.href = "/resume?key=" + key;
                    resumeButton.appendChild(materialIcon("play_arrow"));

                    const skipButton = document.createElement("a");
                    skipButton.className = "button";
                    skipButton.href = "/skip?key=" + key;
                    skipButton.appendChild(materialIcon("skip_next"));

                    const stopButton = document.createElement("a");
                    stopButton.className = "button";
                    stopButton.href = "/stop?key=" + key;
                    stopButton.appendChild(materialIcon("stop"));

                    const repeatButton = document.createElement("a");
                    repeatButton.className = "button";
                    repeatButton.href = "/repeat?key=" + key;
                    repeatButton.appendChild(materialIcon("loop"));

                    const shuffleButton = document.createElement("a");
                    shuffleButton.className = "button";
                    shuffleButton.href = "/shuffle?key=" + key;
                    shuffleButton.appendChild(materialIcon("shuffle"));

                    controlButtons.append(
                        pauseButton,
                        resumeButton,
                        skipButton,
                        stopButton,
                        repeatButton,
                        shuffleButton,
                    );
                }

                const description = document.createElement("span");
                description.id = "track-description";
                description.innerText = data["description"];

                d.append(thumbnail, title, controlButtons, description);
            }
        }
    );

    const url = "wss://" + document.location.host + "/audio-control/status?key=" + key;
    var reconnect = true;

    /**
     * Handle messages from the websocket
     * 
     * @param {MessageEvent} messageEvent The incoming message
     * 
     * @return {void}
     */
    function onmessage(messageEvent) {
        if (messageEvent.data == "END") {
            toAudioControl(key)
        } else if (messageEvent.data == "DISCONNECTED") {
            reconnect = false;
        }
    };

    /**
     * Handle the CLOSE event from the websocket
     * 
     * @param {CloseEvent} closeEvent The CLOSE event
     * 
     * @return {void}
     */
    function onclose(closeEvent) {
        var message = "Websocket closed.";
        if (reconnect) message += " Attempting to reconnect...";

        console.log(message);
        console.log(closeEvent);

        if (reconnect) wsConnect(url, onmessage, onclose);
    }

    wsConnect(url, onmessage, onclose);
}
