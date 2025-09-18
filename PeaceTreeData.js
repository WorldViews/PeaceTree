// PeaceTreeData encapsulates long‑term data loading from DATA_LOG.json
class PeaceTreeData {
    constructor(postHandler = null) {
        this.postHandler = postHandler;
    }

    setPostHandler(handler) {
        this.postHandler = handler;
    }
    clearPostHandler() {
        this.postHandler = null;
    }

    // This method loads all data at once, breaks it into lines,
    // groups the lines into JSON texts, and parses each JSON text.
    async fetchData() {
        console.log("Fetching long-term data from DATA_LOG.json...");
        this.startTime = Date.now() / 1000;
        const response = await fetch('DATA_LOG.json');
        const data = await response.text();
        const jsonLines = data.split('\n').filter(line => line.trim() !== '');
        console.log("Num split lines:", jsonLines.length);

        this.numLines = 0;
        this.numJSONs = 0;
        this.postEvents = [];
        this.partialLine = null;
        this.numMultilineJSONs = 0;
        this.numBadJSONs = 0;

        jsonLines.forEach(line => {
            this.handleLine(line);
        });
        this.finish();
        return this.postEvents;
    }

    async streamData() {
        console.log("Streaming long-term data from DATA_LOG.json...");
        this.startTime = Date.now() / 1000;
        this.numLines = 0;
        this.numJSONs = 0;
        this.postEvents = [];
        this.partialLine = null;          // for multi-line JSON objects (original behavior)
        this.numMultilineJSONs = 0;
        this.numBadJSONs = 0;

        const response = await fetch('DATA_LOG.json');
        if (!response.body) {
            console.warn("No stream body available; falling back to full fetch.");
            const all = await response.text();
            this._processCompleteText(all);
            this.finish();
            return this.postEvents;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";                  // holds chunk remainders that didn't end with '\n'

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Extract complete lines
            let nlIndex;
            while ((nlIndex = buffer.indexOf('\n')) !== -1) {
                const rawLine = buffer.slice(0, nlIndex);
                buffer = buffer.slice(nlIndex + 1);
                this.handleLine(rawLine);
            }
        }

        // Flush any remaining text (last line without newline)
        if (buffer.trim().length > 0) {
            this.handleLine(buffer);
        }

        this.finish();
        return this.postEvents;
    }

    // Helper used if streaming not available
    _processCompleteText(text) {
        const lines = text.split('\n');
        for (const line of lines) {
            if (line.trim() === "") continue;
            this.handleLine(line);
        }
    }

    handleLine(line) {
        this.numLines++;

        // Reassemble multi-line JSON blocks (original semantics preserved)
        if (this.partialLine) {
            this.partialLine += line;
            if (line.trim() === '}') {
                line = this.partialLine;
                this.partialLine = null;
            } else {
                return;
            }
        } else if (line.trim() === "{") {
            this.partialLine = line;
            this.numMultilineJSONs++;
            return;
        }

        try {
            this.numJSONs++;
            const evObj = JSON.parse(line);
            if (evObj.post == null) {
                // skip non-post events
                return;
            }
            if (!evObj.type) {
                evObj.type = "post";
            }
            this.postEvents.push(evObj);
            if (this.postHandler) {
                this.postHandler(evObj);
            }
        } catch (err) {
            console.error("Error loading post:", err);
            console.log("Invalid JSON on line:", this.numLines);
            this.numBadJSONs++;
        }
    }

    finish() {
        const endTime = Date.now() / 1000;
        // Fixed: previously referenced undefined variable 'posts'
        console.log("Num lines read:", this.numLines);
        console.log("Num JSONs read:", this.numJSONs);
        console.log("Num multiline JSONs:", this.numMultilineJSONs);
        console.log("Num bad JSONs:", this.numBadJSONs);
        console.log("Loaded posts count:", this.postEvents.length);
        // show num read in num secs, with 3 decimal places accuracy
        console.log(`Loaded ${this.postEvents.length} posts in ${(endTime - this.startTime).toFixed(3)} secs`);
    }

}