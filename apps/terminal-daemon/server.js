const http = require('http');
const express = require('express');
const cors = require('cors');
const { WebSocketServer } = require('ws');
const os = require('os');
const pty = require('node-pty');
const { v4: uuidv4 } = require('uuid');

// Constants
const MAX_BYTES = 2 * 1024 * 1024; // 2MB per session
const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 minutes in milliseconds

// Security check: ensure process runs as non-root
if (process.getuid && process.getuid() === 0) {
  console.error('[kyros-daemon] ERROR: Process must not run as root for security reasons');
  process.exit(1);
}

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/term" });

wss.on("connection", (socket) => {
  const sessionId = uuidv4();
  let shell = os.platform() === "win32" ? "powershell.exe" : process.env.SHELL || "bash";
  let cols = 80, rows = 24;
  let p = null;
  let bytesSent = 0;
  let lastInputTime = Date.now();
  let inactivityTimer = null;

  console.log(`[kyros-daemon] Session started: ${sessionId}`);

  const resetInactivityTimer = () => {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
    }
    lastInputTime = Date.now();
    inactivityTimer = setTimeout(() => {
      console.log(`[kyros-daemon] Session ${sessionId} timed out due to inactivity`);
      if (p) {
        try { p.kill(); } catch {}
      }
      socket.close();
    }, INACTIVITY_TIMEOUT);
  };

  const checkByteLimit = (data) => {
    bytesSent += data.length;
    if (bytesSent > MAX_BYTES) {
      console.log(`[kyros-daemon] Session ${sessionId} exceeded byte limit (${bytesSent}/${MAX_BYTES})`);
      if (p) {
        try { p.kill(); } catch {}
      }
      socket.close();
      return false;
    }
    return true;
  };

  const cleanup = () => {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
    }
    if (p) {
      try { p.kill(); } catch {}
    }
    console.log(`[kyros-daemon] Session ended: ${sessionId} (bytes sent: ${bytesSent})`);
  };

  socket.on("message", (raw) => {
    try {
      const msg = JSON.parse(raw.toString());
      if (msg.type === "spawn") {
        if (msg.shell && msg.shell !== "auto") shell = msg.shell;
        cols = msg.cols || cols; rows = msg.rows || rows;
        p = pty.spawn(shell, [], { name: "xterm-color", cols, rows, cwd: process.cwd(), env: process.env });
        p.onData((d) => {
          if (checkByteLimit(d)) {
            socket.send(Buffer.from(d));
          }
        });
        p.onExit(({ exitCode }) => {
          socket.send(JSON.stringify({ type: "exit", code: exitCode }));
          cleanup();
        });
        resetInactivityTimer();
      } else if (msg.type === "input" && p) { 
        p.write(msg.data);
        resetInactivityTimer();
      }
      else if (msg.type === "resize" && p) { 
        p.resize(msg.cols, msg.rows); 
        socket.send(JSON.stringify({ type: "resize", cols: msg.cols, rows: msg.rows })); 
      }
    } catch {}
  });
  
  socket.on("close", cleanup);
});

const PORT = process.env.KYROS_DAEMON_PORT || 8787;
server.listen(PORT, "127.0.0.1", () => console.log(`[kyros-daemon] ws://127.0.0.1:${PORT}/term`));