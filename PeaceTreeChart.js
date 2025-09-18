// High-DPI, crisp event bars and axes.
// Expects globals: postEvents (array), getCurrentClockTime(), loadLongTermData (optional)
class PeaceTreeChart {
    constructor() {
        const chartDiv = document.getElementById('chart');
        this.canvas = document.createElement('canvas');
        // CSS size; backing store is set in resizeCanvas()
        this.canvas.style.width = '90%';
        this.canvas.style.height = '160px';
        chartDiv.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');
        this.viewDuration = 3600; // seconds
        this.width = 0;   // CSS px
        this.height = 0;  // CSS px
        this.dpr = 1;

        this.eventBarWidth = 3; // thickness (in CSS px) for event lines. Try 2–4.

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const dpr = Math.max(1, window.devicePixelRatio || 1);
        const displayWidth = Math.max(1, Math.floor(this.canvas.clientWidth || 600));
        const displayHeight = Math.max(
            1,
            Math.floor(parseFloat(getComputedStyle(this.canvas).height) || 160)
        );

        const needResize =
            this.canvas.width !== Math.floor(displayWidth * dpr) ||
            this.canvas.height !== Math.floor(displayHeight * dpr) ||
            this.dpr !== dpr;

        if (needResize) {
            this.canvas.width = Math.floor(displayWidth * dpr);
            this.canvas.height = Math.floor(displayHeight * dpr);
            this.width = displayWidth;
            this.height = displayHeight;
            this.dpr = dpr;

            this.ctx.setTransform(1, 0, 0, 1, 0, 0);
            this.ctx.scale(dpr, dpr);           // 1 unit == 1 CSS px
            this.ctx.imageSmoothingEnabled = false;
        }
    }

    zoom(zf = 1.2) {
        this.viewDuration = Math.max(1, this.viewDuration * zf);
        this.draw();
    }

    async setViewDuration(seconds) {
        if (seconds > 69 && typeof loadLongTermData === 'function') {
            await loadLongTermData();
        }
        this.viewDuration = Math.max(1, seconds);
        this.draw();
    }

    async setViewFull() {
        if (typeof loadLongTermData === 'function') {
            await loadLongTermData();
        }
        if (!postEvents || postEvents.length === 0) return;
        const now = getCurrentClockTime();
        const oldest = postEvents[postEvents.length - 1];
        const oldestPt = typeof oldest.pt === 'number'
            ? oldest.pt
            : Math.floor(new Date(oldest.post?.createdAt).getTime() / 1000);
        this.viewDuration = Math.max(60, now - oldestPt + 60);
        this.draw();
    }

    draw() {
        this.resizeCanvas(); // ensure high-DPI sizing before drawing
        this.ct = getCurrentClockTime();
        this.ctx.clearRect(0, 0, this.width, this.height);
        this.drawAxes();
        this.drawEvents();
    }

    drawAxes() {
        const w = this.width, h = this.height;
        this.ctx.save();
        this.ctx.lineWidth = 1;
        this.ctx.strokeStyle = '#000';
        this.ctx.beginPath();
        // half-pixel alignment for crisp 1px strokes
        this.ctx.moveTo(0.5, 0.5);
        this.ctx.lineTo(0.5, h - 0.5);
        this.ctx.lineTo(w - 0.5, h - 0.5);
        this.ctx.stroke();
        this.ctx.restore();
    }

    drawEvents() {
        if (!postEvents || postEvents.length === 0) return;

        const w = this.width, h = this.height;
        const dur = this.viewDuration;
        const now = this.ct;

        this.ctx.save();
        this.ctx.lineWidth = 1;

        for (const ev of postEvents) {
            const pt = typeof ev.pt === 'number'
                ? ev.pt
                : Math.floor(new Date(ev.post?.createdAt).getTime() / 1000);
            if (!Number.isFinite(pt)) continue;

            const dt = now - pt;
            if (dt < 0) continue;

            // Map to CSS px and snap to an integer-centered thicker bar
            let x = (dt / dur) * w;
            x = Math.max(1, Math.min(w - 1, x));
            const xCenter = Math.round(x);

            const barW = (this.eventBarWidth | 0) || 1; // ensure integer >=1
            const half = Math.floor(barW / 2);
            let xLeft = xCenter - half;
            if (xLeft < 1) xLeft = 1;
            if (xLeft + barW > w - 1) xLeft = Math.max(1, (w - 1) - barW);

            const rate = ev.rate || 10;
            const barH = Math.max(1, Math.min(h - 2, Math.round(rate)));

            let color = 'black';
            if (ev.type === 'rtweb_post' || ev.type === 'rtpost') color = 'blue';
            else if (ev.type === 'reply') color = 'green';

            this.ctx.fillStyle = color;
            // Draw a thicker, still crisp, integer-aligned bar
            this.ctx.fillRect(xLeft, h - 2 - barH, barW, barH);
        }

        this.ctx.restore();
    }
}