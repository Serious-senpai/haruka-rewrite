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
 * Create a websocket connection
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
 * Append a child to an element
 * 
 * @param {HTMLElement} parent The parent element
 * @param {string} tagName The child's tag name to append
 * 
 * @return {HTMLElement} The added child element
 */
function appendChild(parent, tagName) {
    const child = document.createElement(tagName);
    parent.appendChild(child);
    return child;
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
    element.innerText = content;
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
        d.appendChild(createHeading("h3", "IMAGE GENERATOR"));

        const container = appendChild(d, "div");
        container.id = "random-image-container";
        {
            const image = document.createElement("img")
            image.alt = "image";
            image.id = "random-image";
            image.src = "/collection/random?time=" + Date.now();
            container.appendChild(image);
        }

        const reloadButton = appendChild(d, "button")
        reloadButton.id = "reload-button";
        reloadButton.type = "button";
        reloadButton.onclick = toImageGenerator;
        reloadButton.appendChild(materialIcon("refresh"));
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
        d.appendChild(createHeading("h3", "PIXIV USER SEARCH"));

        const form = appendChild(d, "form");
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
    var reconnect = true;

    /**
     * @param {MessageEvent} messageEvent
     */
    function onMessage(messageEvent) {
        if (messageEvent.data == "END") {
            console.log("Track ended at " + Date.now());
            buildAudioControlPage(key);
        } else if (messageEvent.data == "DISCONNECTED") {
            reconnect = false;
            console.log("Voice client disconnected at " + Date.now());
        }
    }

    /**
     * @param {CloseEvent} closeEvent
     */
    function onClose(closeEvent) {
        var message = "WebSocket closed at " + Date.now();
        if (reconnect) {
            message += "\nAttempting to reconnect.";
            connect();
        }
        console.log(message);
    }

    function connect() {
        wsConnect("wss://" + document.location.host + "/audio-control/status?key=" + key, onMessage, onClose);
    }

    connect();
    buildAudioControlPage(key);
}


function buildAudioControlPage(key) {
    getAsync(
        "/audio-control/playing?key=" + key,
        (request) => {
            if (request.status != 200) return;

            const data = JSON.parse(request.responseText);

            const d = initializeMain();
            {
                const thumbnail = appendChild(d, "img");
                thumbnail.alt = "Track thumbnail";
                thumbnail.id = "track-thumbnail";
                thumbnail.src = data["thumbnail"];

                d.appendChild(createHeading("h3", data["title"]));

                const controlButtons = appendChild(d, "div");
                controlButtons.id = "control-buttons";
                {
                    const pauseButton = appendChild(controlButtons, "a")
                    pauseButton.className = "button";
                    pauseButton.href = "/pause?key=" + key;
                    pauseButton.title = "Pause";
                    pauseButton.appendChild(materialIcon("pause"));

                    const resumeButton = appendChild(controlButtons, "a")
                    resumeButton.className = "button";
                    resumeButton.href = "/resume?key=" + key;
                    resumeButton.title = "Resume";
                    resumeButton.appendChild(materialIcon("play_arrow"));

                    const skipButton = appendChild(controlButtons, "a");
                    skipButton.className = "button";
                    skipButton.href = "/skip?key=" + key;
                    skipButton.title = "Skip";
                    skipButton.appendChild(materialIcon("skip_next"));

                    const stopButton = appendChild(controlButtons, "a");
                    stopButton.className = "button";
                    stopButton.href = "/stop?key=" + key;
                    stopButton.title = "Stop";
                    stopButton.appendChild(materialIcon("stop"));

                    const repeatButton = appendChild(controlButtons, "a");
                    repeatButton.className = "button";
                    repeatButton.href = "/repeat?key=" + key;
                    repeatButton.title = "Toggle repeat";
                    repeatButton.appendChild(materialIcon("loop"));

                    const shuffleButton = appendChild(controlButtons, "a");
                    shuffleButton.className = "button";
                    shuffleButton.href = "/shuffle?key=" + key;
                    shuffleButton.title = "Toggle shuffle";
                    shuffleButton.appendChild(materialIcon("shuffle"));

                    const stopafterButton = appendChild(controlButtons, "a");
                    stopafterButton.className = "button";
                    stopafterButton.href = "/stopafter?key=" + key;
                    stopafterButton.title = "Toggle stopafter";
                    stopafterButton.appendChild(materialIcon("last_page"));
                }

                appendChild(d, "br");

                const description = appendChild(d, "span");
                description.id = "track-description";
                description.innerText = data["description"];
            }
        }
    );
}