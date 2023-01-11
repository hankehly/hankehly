/*
 * Call a function max once per `time` interval
*/
let throttleTimer;
const throttle = (callback, time) => {
    if (throttleTimer) {
        return;
    }
    throttleTimer = true;
    setTimeout(() => {
        callback();
        throttleTimer = false;
    }, time);
}

/*
 * Divides the screen into `n` squares (0-n) and returns the square number corresponding to XY in rect.
 * rect: DOMRect of bounding box
 * pageX: integer X location of target
 * pageY: integer Y location of target
 * n: integer number of desired squares
*/
function getSquarePositionInRect(rect, pageX, pageY, n) {
    const xStepSize = rect.width / n;
    const xPos = Math.floor(pageX / xStepSize);
    const yStepSize = rect.height / n;
    const yPos = Math.floor(pageY / yStepSize);
    const square = xPos + yPos * n;
    return square;
}

const faceDirectionMap3x3 = [
    "left", "up", "right",
    "left", "front", "right",
    "left", "front", "right",
];

const faceImageMap = {
    "left": "face-left.png",
    "up": "face-up.png",
    "front": "face-front.gif",
    "right": "face-right.png"
};

window.onpointermove = function (e) {
    throttle(function () {
        const rect = document.getElementById("header").getBoundingClientRect();
        const faceEl = document.getElementById("face");
        const defaultImage = "img/" + faceImageMap["front"];
        if (e.pageY > rect.height) {
            if (faceEl.getAttribute("src") !== defaultImage) {
                faceEl.setAttribute("src", defaultImage);
            }
        } else {
            const pos = getSquarePositionInRect(rect, e.pageX, e.pageY, 3);
            const faceDirection = faceDirectionMap3x3[pos];
            const faceImage = "img/" + faceImageMap[faceDirection];
            faceEl.setAttribute("src", faceImage);
            console.log(document.getElementById("header").getBoundingClientRect());
            console.log("pageX: " + e.pageX + ", pageY: " + e.pageY);
        }
    }, 75);
};
