// Provides a global playGongSound() without relying on page globals.
(function () {
    let audioContext = null;

    function ensureAudioContext() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioContext;
    }

    window.playGongSound = function playGongSound() {
        const ac = ensureAudioContext();

        const duration = 3; // seconds
        const sampleRate = ac.sampleRate;
        const buffer = ac.createBuffer(1, duration * sampleRate, sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < buffer.length; i++) {
            const t = i / sampleRate;
            const envelope = Math.exp(-t * 2); // Exponential decay

            const fundamental = 220;
            let sample = 0;
            sample += Math.sin(2 * Math.PI * fundamental * t) * 0.3;
            sample += Math.sin(2 * Math.PI * fundamental * 1.5 * t) * 0.2;
            sample += Math.sin(2 * Math.PI * fundamental * 2.2 * t) * 0.15;
            sample += Math.sin(2 * Math.PI * fundamental * 3.1 * t) * 0.1;
            sample += Math.sin(2 * Math.PI * fundamental * 4.7 * t) * 0.05;

            sample += (Math.random() - 0.5) * 0.02 * envelope;

            data[i] = sample * envelope * 0.3;
        }

        const source = ac.createBufferSource();
        source.buffer = buffer;

        const gainNode = ac.createGain();
        gainNode.gain.setValueAtTime(0.7, ac.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + duration);

        source.connect(gainNode);
        gainNode.connect(ac.destination);
        source.start();
    };
})();