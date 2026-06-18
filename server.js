"use strict";

/*
 * Examify — zero-dependency static file server.
 * Serves the app folder over HTTP, bound to all network interfaces so other
 * devices on the same Wi-Fi/LAN can reach it via this machine's local IP.
 *
 *   node server.js            (defaults to port 8000)
 *   PORT=3000 node server.js  (custom port)
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const os = require("os");

const PORT = parseInt(process.env.PORT, 10) || 8888;
const ROOT = __dirname;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".pdf": "application/pdf",
};

const server = http.createServer((req, res) => {
  // Strip query string, decode, and normalize to prevent path traversal.
  let urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
  if (urlPath === "/") urlPath = "/index.html";

  const filePath = path.normalize(path.join(ROOT, urlPath));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    return res.end("Forbidden");
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      return res.end("404 Not Found");
    }
    const type =
      MIME[path.extname(filePath).toLowerCase()] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": type });
    res.end(data);
  });
});

function lanAddresses() {
  const out = [];
  const ifaces = os.networkInterfaces();
  for (const name of Object.keys(ifaces)) {
    for (const ni of ifaces[name] || []) {
      if (ni.family === "IPv4" && !ni.internal) out.push(ni.address);
    }
  }
  return out;
}

server.listen(PORT, "0.0.0.0", () => {
  console.log("\n  Examify is running. Open one of these:\n");
  console.log("    Local:    http://localhost:" + PORT);
  for (const ip of lanAddresses()) {
    console.log(
      "    Network:  http://" +
        ip +
        ":" +
        PORT +
        "   (other devices on this Wi-Fi)",
    );
  }
  console.log("\n  Press Ctrl+C to stop.\n");
});

server.on("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(
      "Port " + PORT + " is already in use. Try: PORT=3000 node server.js",
    );
  } else {
    console.error(err);
  }
  process.exit(1);
});
