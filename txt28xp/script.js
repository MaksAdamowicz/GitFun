import Lib from 'https://esm.sh/ticalc-usb';
const { ticalc, tifiles } = Lib;

document.addEventListener('DOMContentLoaded', async () => {
    // Elements
    const fileInput = document.getElementById('fileInput');
    const notesInput = document.getElementById('notesInput');
    const clearBtn = document.getElementById('clearBtn');
    const charCount = document.getElementById('charCount');
    const lineCount = document.getElementById('lineCount');
    const progName = document.getElementById('progName');
    const nameLen = document.getElementById('nameLen');
    const wrapSelect = document.getElementById('wrapSelect');
    const customWrapGroup = document.getElementById('customWrapGroup');
    const customWrapWidth = document.getElementById('customWrapWidth');
    const sanitizeToggle = document.getElementById('sanitizeToggle');
    const convertBtn = document.getElementById('convertBtn');
    
    const dropZone = document.getElementById('dropZone');
    const calcScreenHeader = document.querySelector('.calc-program-header');
    const calcContent = document.getElementById('calcContent');
    
    const btnFontCE = document.getElementById('btnFontCE');
    const btnFontClassic = document.getElementById('btnFontClassic');

    // USB Elements
    const connectUsbBtn = document.getElementById('connectUsbBtn');
    const usbStatusText = document.getElementById('usbStatusText');
    const statusDot = document.querySelector('.status-dot');
    const autoSyncGroup = document.querySelector('.auto-sync-group');
    const autoSyncToggle = document.getElementById('autoSyncToggle');

    // State
    let wrapWidth = 26; // Default to TI-84 Plus CE (26 cols)
    let activeCalculator = null;

    // Helper: Enforce TI-84 Program Name Rules
    function validateProgName() {
        let value = progName.value.toUpperCase();
        // Keep only alphanumeric
        value = value.replace(/[^A-Z0-9]/g, '');
        
        // Ensure starts with a letter
        if (value.length > 0 && !/^[A-Z]/.test(value)) {
            // Remove digits at the start
            value = value.replace(/^[0-9]+/, '');
        }

        // Limit to 8 characters
        if (value.length > 8) {
            value = value.substring(0, 8);
        }

        progName.value = value;
        nameLen.textContent = `${value.length}/8`;
        
        // Update calculator header
        calcScreenHeader.textContent = `PROGRAM:${value || 'UNTITLED'}`;

        // Disable convert if empty
        if (value.length === 0) {
            progName.style.borderColor = '#ef4444';
            convertBtn.disabled = true;
        } else {
            progName.style.borderColor = '';
            convertBtn.disabled = false;
        }
    }

    // Helper: Decompose accents (JS equivalent of NFKD normalize)
    function cleanAccents(str) {
        return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    // Helper: Replace smart/curly punctuation
    function replaceSmartPunctuation(str) {
        const replacements = {
            '“': '"', '”': '"',
            '‘': "'", '’': "'",
            '–': '-', '—': '-',
            '…': '...',
        };
        return str.replace(/[“”‘’–—…]/g, m => replacements[m] || m);
    }

    // Helper: Sanitize text for TI calculator encoding (filtering out unsupported)
    function softSanitize(str) {
        if (!sanitizeToggle.checked) return str;
        
        let cleaned = replaceSmartPunctuation(str);
        cleaned = cleanAccents(cleaned);
        
        // Keep letters, numbers, standard spaces, newlines, and basic symbols
        return cleaned.replace(/[^\x20-\x7E\n\r\t]/g, '');
    }

    // Helper: Wrap lines to wrapWidth
    function wrapText(text, width) {
        if (width <= 0) return text;

        const lines = text.split(/\r?\n/);
        const wrappedLines = [];

        lines.forEach(line => {
            if (line.trim() === '') {
                wrappedLines.push('');
                return;
            }

            let currentLine = line;
            while (currentLine.length > 0) {
                if (currentLine.length <= width) {
                    wrappedLines.push(currentLine);
                    break;
                }

                // Try to split on space
                let splitIdx = currentLine.lastIndexOf(' ', width);
                if (splitIdx <= 0) {
                    splitIdx = width;
                }

                wrappedLines.push(currentLine.substring(0, splitIdx));
                currentLine = currentLine.substring(splitIdx).trimStart();
            }
        });

        return wrappedLines.join('\n');
    }

    // Update real-time counters & calculator screen preview
    function updatePreview() {
        const text = notesInput.value;
        
        // 1. Update counts
        charCount.textContent = `${text.length} character${text.length !== 1 ? 's' : ''}`;
        const lines = text ? text.split(/\r?\n/).length : 0;
        lineCount.textContent = `${lines} line${lines !== 1 ? 's' : ''}`;

        // 2. Process for preview
        let previewText = softSanitize(text);
        
        // Handle wrap width
        if (wrapSelect.value === 'custom') {
            wrapWidth = parseInt(customWrapWidth.value) || 26;
        } else {
            wrapWidth = parseInt(wrapSelect.value);
        }

        if (wrapWidth > 0) {
            previewText = wrapText(previewText, wrapWidth);
        }

        // 3. Render inside calculator screen
        calcContent.textContent = previewText;
    }

    // Drag and Drop Handling
    function handleFile(file) {
        if (!file || !file.name.endsWith('.txt')) {
            alert('Please select a valid plain text (.txt) file.');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            notesInput.value = e.target.result;
            
            // Auto-detect program name from filename
            let name = file.name.substring(0, file.name.lastIndexOf('.'));
            name = name.replace(/[^A-Za-z0-9]/g, '').toUpperCase().substring(0, 8);
            if (name && /^[A-Z]/.test(name)) {
                progName.value = name;
            }
            
            validateProgName();
            updatePreview();
        };
        reader.readAsText(file);
    }

    // Trigger base64 download
    function download8xpFile(filename, base64Data) {
        const binaryString = window.atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }

    // USB Connection UI Helper
    function updateUsbStatus(connected, name = "") {
        if (connected) {
            statusDot.classList.add('connected');
            usbStatusText.textContent = name ? `Connected: ${name}` : 'Connected';
            connectUsbBtn.textContent = "Disconnect";
            connectUsbBtn.classList.remove('btn-secondary');
            connectUsbBtn.classList.add('btn-primary');
            autoSyncGroup.style.display = 'flex';
            
            convertBtn.querySelector('span').textContent = "Send to Calculator ⚡";
            convertBtn.classList.add('btn-glow-green');
        } else {
            statusDot.classList.remove('connected');
            usbStatusText.textContent = 'Not connected';
            connectUsbBtn.textContent = "Connect Calculator";
            connectUsbBtn.classList.remove('btn-primary');
            connectUsbBtn.classList.add('btn-secondary');
            autoSyncGroup.style.display = 'none';
            
            convertBtn.querySelector('span').textContent = "Generate .8XP File";
            convertBtn.classList.remove('btn-glow-green');
        }
    }

    // WebUSB Integration via ticalc-usb
    if (navigator.usb) {
        try {
            await ticalc.init();
            
            ticalc.addEventListener('connect', (calculator) => {
                activeCalculator = calculator;
                updateUsbStatus(true, calculator.name);
            });
            
            ticalc.addEventListener('disconnect', () => {
                activeCalculator = null;
                updateUsbStatus(false);
            });
            
            // Try to bind already connected calculators
            const connectedDevices = await navigator.usb.getDevices();
            if (connectedDevices.length > 0) {
                // Device exists and might be pre-authorized, let's wait for the connect event
                // which is triggered by ticalc.init() automatically.
            }
        } catch (err) {
            console.error("ticalc init error:", err);
        }
    } else {
        usbStatusText.textContent = "WebUSB not supported in this browser.";
        connectUsbBtn.disabled = true;
        connectUsbBtn.style.opacity = '0.5';
    }

    // USB Connect Button Event
    connectUsbBtn.addEventListener('click', async () => {
        try {
            if (activeCalculator) {
                activeCalculator = null;
                updateUsbStatus(false);
            } else {
                connectUsbBtn.textContent = "Connecting...";
                connectUsbBtn.disabled = true;
                await ticalc.choose();
            }
        } catch (err) {
            console.error("Connection failed:", err);
            alert("Could not connect to calculator. Make sure it is connected, turned on, and that no other software (like TI Connect) is currently using its connection.");
        } finally {
            if (!activeCalculator) {
                connectUsbBtn.textContent = "Connect Calculator";
                connectUsbBtn.disabled = false;
            }
        }
    });

    // Event Listeners
    notesInput.addEventListener('input', updatePreview);
    progName.addEventListener('input', validateProgName);
    
    clearBtn.addEventListener('click', () => {
        notesInput.value = '';
        updatePreview();
        notesInput.focus();
    });

    wrapSelect.addEventListener('change', () => {
        if (wrapSelect.value === 'custom') {
            customWrapGroup.style.display = 'flex';
        } else {
            customWrapGroup.style.display = 'none';
        }
        
        const val = wrapSelect.value;
        if (val === '16') {
            btnFontClassic.classList.add('active');
            btnFontCE.classList.remove('active');
        } else if (val === '26') {
            btnFontCE.classList.add('active');
            btnFontClassic.classList.remove('active');
        }
        
        updatePreview();
    });

    customWrapWidth.addEventListener('input', updatePreview);
    sanitizeToggle.addEventListener('change', updatePreview);

    // Font Toggles on the calculator body
    btnFontCE.addEventListener('click', () => {
        btnFontCE.classList.add('active');
        btnFontClassic.classList.remove('active');
        wrapSelect.value = '26';
        customWrapGroup.style.display = 'none';
        updatePreview();
    });

    btnFontClassic.addEventListener('click', () => {
        btnFontClassic.classList.add('active');
        btnFontCE.classList.remove('active');
        wrapSelect.value = '16';
        customWrapGroup.style.display = 'none';
        updatePreview();
    });

    // File Upload Inputs
    fileInput.addEventListener('change', (e) => {
        handleFile(e.target.files[0]);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag-over styling
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    });

    // API Call & Convert
    convertBtn.addEventListener('click', async () => {
        const text = notesInput.value.trim();
        if (!text) {
            alert('Please enter some text in the editor before generating!');
            return;
        }

        let name = progName.value.trim().toUpperCase();
        if (!name) {
            name = 'NOTES';
        }

        let width = 0;
        if (wrapSelect.value === 'custom') {
            width = parseInt(customWrapWidth.value) || 26;
        } else {
            width = parseInt(wrapSelect.value);
        }

        const payload = {
            text: notesInput.value,
            name: name,
            wrap_width: width,
            sanitize: sanitizeToggle.checked
        };

        // UI Feedback: Loading state
        convertBtn.disabled = true;
        const origText = convertBtn.querySelector('span').textContent;
        convertBtn.querySelector('span').textContent = activeCalculator && autoSyncToggle.checked ? 'Sending to Calculator...' : 'Generating...';

        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (result.success) {
                // If calculator is connected, transfer directly!
                if (activeCalculator && autoSyncToggle.checked) {
                    try {
                        const binaryString = window.atob(result.data);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }

                        // Parse and validate using ticalc-usb's tifiles
                        const parsedFile = tifiles.parseFile(bytes);
                        if (!tifiles.isValid(parsedFile)) {
                            throw new Error("Parsed file is invalid.");
                        }

                        // Send the file over USB
                        await activeCalculator.sendFile(parsedFile);
                        alert(`Successfully sent "${result.filename}" directly to your calculator!`);
                    } catch (err) {
                        console.error('Direct transfer error:', err);
                        alert(`Direct transfer failed: ${err.message || err}. Downlading the file as backup.`);
                        download8xpFile(result.filename, result.data);
                    }
                } else {
                    // Fallback to downloading the file
                    download8xpFile(result.filename, result.data);
                }
                
                // Show sanitized result in preview
                if (result.text) {
                    calcContent.textContent = result.text;
                }
            } else {
                alert(`Error during conversion: ${result.error}`);
            }
        } catch (err) {
            console.error('Fetch error:', err);
            alert('Could not connect to the backend server. Make sure server.py is running!');
        } finally {
            convertBtn.disabled = false;
            convertBtn.querySelector('span').textContent = origText;
        }
    });

    // Initializations
    validateProgName();
    updatePreview();
});
