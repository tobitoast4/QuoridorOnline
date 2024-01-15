var canvas = document.querySelector("canvas");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

var c = canvas.getContext("2d");

function clear(){
    c.clearRect(0, 0, innerWidth, innerHeight)
}

var mouse = {
    x: undefined,
    y: undefined
}

document.addEventListener("mouseleave", function(event) {
    if(event.clientY <= 0 || event.clientX <= 0 || (event.clientX >= window.innerWidth || event.clientY >= window.innerHeight)) {
        mouse.x = undefined;
        mouse.y = undefined;
    }
});

window.addEventListener("mousemove", function(event) {
    mouse.x = event.x;
    mouse.y = event.y;
});

window.addEventListener("resize", function(event) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    init();
})


function Circle(x, y, dx, dy, radius){
    this.radius = radius;

    this.x = x;
    this.y = y;
    this.dx = dx;
    this.dy = dy;

    this.draw = function() {
        c.beginPath();
        c.arc(this.x, this.y, this.radius, 0, 2 * Math.PI);
        c.strokeStyle = "black";
        c.fillStyle = "white";
        c.stroke();
        c.fill();
    }

    this.update = function() {
        if(this.x + this.radius >= innerWidth || this.x - this.radius <= 0){
            this.dx = -this.dx;
        }
        
        if(this.y + this.radius >= innerHeight || this.y - this.radius <= 0){
            this.dy = -this.dy;
        }
    
        this.x += this.dx;
        this.y += this.dy;

        // interactivity
        if (mouse.x - this.x < 50 && mouse.x - this.x > -50 &&
            mouse.y - this.y < 50 && mouse.y - this.y > -50){
            if (this.radius < 10){
                this.radius += 2;
            }
        } else {
            if (this.radius > 5){
                this.radius -= 2;
            }
        }

        this.draw();
    }
}


var circles = [];

function init() {
    
    amount_circles = window.innerWidth / 50;
    circles = [];

    for (var i = 0; i < amount_circles; i++){
        var radius = 5;
        var x = Math.random() * (innerWidth - radius * 2) + radius;
        var y = Math.random() * (innerHeight - radius * 2) + radius;
        var dx = (Math.random() - 0.5) * 0.01;
        if (dx >= 0){
            dx += 0.5;
        } else {
            dx -= 0.5;
        }
        var dy = (Math.random() - 0.5) * 0.01;
        if (dy >= 0){
            dy += 0.5;
        } else {
            dy -= 0.5;
        }
        var circle = new Circle(x, y, dx, dy, radius);
        circles.push(circle);
    }
}


function animate(){
    requestAnimationFrame(animate);
    clear();
    for (var i = 0; i < amount_circles; i++){
        circles[i].update();
    }

}

init();
animate();
