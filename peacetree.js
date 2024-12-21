"use strict";

console.log("in PeaceTree.js");

let useMQTT = false;
let clicks = 0;

function click() {
    console.log("click");
    clicks += 1;
    $("#clicks").html("clicks: " + clicks);
}

function peace() {
    console.log("peace");
    clicks = 0;
    $("#clicks").html("clicks: " + clicks);
    var url = "https://www.reachandteach.com/peacetreelive.php";
    var str = "pray for peace";
    // post to the server
    let form = { prayer: str };
    $.post(url, form, function (data) {
        console.log("posted", form);
        console.log("received", data);
    });
    console.log("posted");
}

// This is a promise based version of code for getting
// JSON.  New code should use this instead of getJSON
// and older code should migrate to this.
async function loadJSON(url) {
    console.log("loadJSON: " + url);
    return new Promise((res, rej) => {
        $.ajax({
            url: url,
            dataType: 'text',
            success: function (str) {
                var data;
                try {
                    data = JSON.parse(str);
                }
                catch (err) {
                    console.log("err: " + err);
                    alert("Error in json for: " + url + "\n" + err);
                    rej(err);
                }
                res(data);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log("Failed to get JSON for " + url);
                rej(errorThrown);
            }
        });
    })
}

function getClockTime() {
    return new Date().getTime() / 1000.0;
}

class PeaceTree  {
    constructor(opts) {
        opts = opts || {};
        this.name = opts.name || "PeaceTree";
        this.w = opts.w || 2.0;
        this.dr = opts.dr || 1.1;
        console.log("PeaceTree ...yup ... opts", opts);
        this.pts = [];
        this.colors = [];
        this.lastRotTime = 0;
        window.PT = this;
        this.value = 0;
        this.dataUrl = "https://io.adafruit.com/api/v2/reachandteach/feeds/peacetree";
       // this.dataUrl = "https://io.adafruit.com/api/v2/donkimber/feeds/bobbletree";
        this.getData();
        this.mqtt = null;
        //useMQTT = true;
        if (useMQTT)
            this.startMQTT();
        else
            this.startPolling();
        //this.startMQTT();
        //this.startPolling();
    }

    startMQTT() {
        var inst = this;
        try {
            this.mqtt = new GardenMQTT();
            this.mqtt.observer = val => inst.noticeVal(val);
            this.mqtt.connect();
            console.log("MQTT started");
        }
        catch (e) {
            console.log("***** Cannot get and connect MQTT", e);
        }
    }

    noticeVal(val) {
        console.log("PeaceTree.noticeVal", val);
        this.value = Number(val);
        $("#score").html("" + this.value);
        this.redraw();
    }

    startPolling() {
        var inst = this;
        this.pollingId = setInterval(() => inst.getData(), 5000);
    }

    async getData() {
        var data = await loadJSON(this.dataUrl);
        console.log("***** PeaceTree score ****", data);
        this.noticeVal(Number(data.last_value));
    }

    tick() {
        var t = getClockTime();
        var dt = t - this.lastRotTime;
        if (dt > 0.5) {
            this.rotate()
            this.lastRotTime = t;
        }
    }

    rotate() {
        console.log("rotate");
    }

    redraw() {
        console.log("redraw");
        var canvas = document.getElementById("canvas");
        var ctx = canvas.getContext("2d");
        // convert last value to color
        var r = Math.floor(this.value);
        var g = 160;
        var b = 100;
        //var color = sprintf("rgb(%d,%d,%d)", r, g, b);
        // produce color using javacript format rather than sprintf
        var color = `rgb(${r},${g},${b})`;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        this.draw(canvas, ctx);
    }

    draw(canvas, ctx) {
        this.pts = [
            [0,0],
            [100,100],
            [200,40]
        ];
        ctx.save();
        //this.drawRect(canvas, ctx, this.x, this.y, 10, 10);
        var t = getClockTime();
        var drawLines = true;
        if (drawLines) {
            var prevPt = this.pts[0];
            ctx.beginPath();
            ctx.lineWidth = 0.2;
            ctx.strokeStyle = 'black';
            for (var i = 1; i < this.pts.length; i++) {
                var pt = this.pts[i];
                ctx.moveTo(prevPt[0], prevPt[1]);
                ctx.lineTo(pt[0], pt[1]);
                prevPt = pt;
            }
            ctx.stroke();
        }
        // draw the name
        ctx.fillStyle = "black";
        ctx.font = "20px Arial";
        let str = this.name + " " + this.value;
        ctx.fillText(str, 10, 20);
        ctx.restore();
    }
}
