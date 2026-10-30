// Camera-based QR scanner for organisers marking attendance.
// Requires html5-qrcode (loaded via CDN in scanner.html) and a
// #qr-reader element plus a data-checkin-url attribute with the
// event's check-in endpoint.

document.addEventListener("DOMContentLoaded", () => {
  const readerEl = document.getElementById("qr-reader");
  const resultEl = document.getElementById("scan-result");
  if (!readerEl) return;

  const checkinUrl = readerEl.dataset.checkinUrl;
  let busy = false;

  const scanner = new Html5Qrcode("qr-reader");

  const onScanSuccess = async (decodedText) => {
    if (busy) return;
    busy = true;

    try {
      const res = await fetch(checkinUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: decodedText }),
      });
      const data = await res.json();
      showResult(data.message, data.ok, data.name);
    } catch (err) {
      showResult("Network error — try again.", false);
    }

    setTimeout(() => { busy = false; }, 1500);
  };

  function showResult(message, ok, name) {
    // Show the registrant's name BIG so the organiser can compare it with the
    // person in front of them (a forwarded QR screenshot carries the original owner's name).
    resultEl.innerHTML = "";
    if (name) {
      const nameEl = document.createElement("div");
      nameEl.textContent = name;
      nameEl.style.cssText = "font-size:1.6rem; font-weight:800; margin-bottom:4px;";
      resultEl.appendChild(nameEl);
    }
    const msgEl = document.createElement("div");
    msgEl.textContent = ok ? "✔ Checked in — confirm this is the person in front of you." : message;
    resultEl.appendChild(msgEl);
    resultEl.style.background = ok ? "rgba(0,229,160,0.15)" : "rgba(255,93,115,0.15)";
    resultEl.style.color = ok ? "#00e5a0" : "#ff5d73";
  }

  scanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 240 },
    onScanSuccess
  ).catch(() => {
    showResult("Couldn't access the camera. Check browser permissions.", false);
  });
});
