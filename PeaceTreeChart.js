// Expects globals: getCurrentClockTime(), postEvents (array)
class PeaceTreeChart {
    constructor() {
        const chartDiv = document.getElementById('chart');
        const canvas = document.createElement('canvas');
        // set width to "90%"
        canvas.style.width = "90%";
        canvas.style.height = "160px";
        chartDiv.appendChild(canvas);
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.width = canvas.width;
        this.height = canvas.height;
        this.viewDuration = 3600; // 1 hour
        //this.draw();
    }

    zoom(zf = 1.2) {
        this.viewDuration *= zf;
        this.draw();
    }

    async setViewDuration(seconds) {
        if (seconds > 69) {
            await loadLongTermData();
        }
        this.viewDuration = seconds;
        this.draw();
    }

    async setViewFull() {
        await loadLongTermData();
        if (postEvents.length === 0) return;
        const now = getCurrentClockTime();
        const oldestPostTime = Math.floor(new Date(postEvents[postEvents.length - 1].post.createdAt).getTime() / 1000);
        this.viewDuration = now - oldestPostTime + 60; // add 60 seconds buffer
        this.draw();
    }

    draw() {
        this.ct = getCurrentClockTime();

        // Clear previous chart
        this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);

        // Draw axes
        this.drawAxes();

        // Draw events
        this.drawEvents();
    }

    drawAxes() {
        // use canvas width and height to determine axis positions
        let w = this.ctx.canvas.width;
        let h = this.ctx.canvas.height;
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(0, h - 1);
        this.ctx.lineTo(w - 1, h - 1);
        this.ctx.stroke();
    }

    // get and draw events from recentEvents
    drawEvents() {
        if (!postEvents || postEvents.length === 0) {
            return;
        }
        for (const event of postEvents) {
            // get width and height
            let cw = this.ctx.canvas.width;
            let ch = this.ctx.canvas.height;

            let r = event.rate || 10;
            let style = "black";
            let pt = event.pt; // event.timestamp in seconds
            if (event.type === "rtweb_post") {
                style = "blue";
            }
            // compute dt:  time in seconds since event.timestamp
            const dt = (this.ct - pt);
            // map dt to x position
            const dur = this.viewDuration;
            const x = 1 + (dt / dur) * cw;
            const y = ch - 2; // Map value to y position
            const w = 0.8;
            const h = r;
            this.ctx.fillStyle = style;
            this.ctx.strokeStyle = style;
            this.ctx.fillRect(x, y - h, w, h);
            this.ctx.strokeRect(x, y - h, w, h);
        }
    }
}