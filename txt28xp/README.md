# TI-84 .8XP Notes Converter

A sleek, premium local web application to convert plain text notes (`.txt` files or copied text) into calculator-readable program files (`.8xp`) for your TI-83 Plus, TI-84 Plus, and TI-84 Plus CE graphing calculators.

Write your study guides, formulas, or cheat sheets on your computer, convert them instantly, and view them directly on your calculator!

## Features

-   **Interactive Text Editor:** Write or paste your notes directly, or drag-and-drop a `.txt` file.
-   **TI-84 Screen Preview:** A real-time calculator screen simulator showing exactly how your text will look on the calculator screen.
-   **Smart Text Sanitizer:** Automatically decomposes unicode accents (e.g., `é` &rarr; `e`), fixes smart curly quotes (`“` &rarr; `"`), and filters out unsupported Z80 characters to prevent calculator file corruption.
-   **Auto-Wrapping:** Automatically wrap text lines to match the TI-84 CE screen (26 characters wide) or the classic TI-84 screen (16 characters wide).
-   **One-Click Download / Direct USB Send:** Download the `.8xp` file locally, or **transfer it directly to your connected calculator** over USB using WebUSB in modern browsers!

## Quick Start

1.  Open your terminal and navigate to this folder:
    ```bash
    cd /Users/maksadamowicz/Desktop/GitFun/txt28xp
    ```
2.  Start the converter server:
    ```bash
    python3 server.py
    ```
3.  Open your web browser and go to:
    **[http://localhost:8000](http://localhost:8000)** (Use Chrome or Edge for USB transfer support).

## Transferring to Calculator

### Method A: Direct WebUSB Transfer (Recommended)
1. Turn on your calculator and connect it to your laptop via USB.
2. Click **Connect Calculator** in the browser dashboard.
3. Select your calculator in the browser's popup window and click **Connect**.
4. Check **Auto-Sync to Calculator** and click **Send to Calculator ⚡**! The program will instantly load onto your device.

### Method B: Manual File Transfer
1. Open the official **TI Connect CE** software on your computer.
2. Connect your calculator via USB.
3. Drag the downloaded `.8xp` file into the **Calculator Explorer** tab of TI Connect CE.
4. On the calculator, press the `[PRGM]` key, select your program, and press `[ENTER]` to view it!
