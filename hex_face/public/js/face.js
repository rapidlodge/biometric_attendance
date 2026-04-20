document.addEventListener('DOMContentLoaded', () => {
  const welcomeScreen = document.getElementById('welcome-screen');
  const scanScreen = document.getElementById('scan-screen');
  const confirmationScreen = document.getElementById('confirmation-screen');

  const clockElement = document.getElementById('clock');
  const dateElement = document.getElementById('date');
  const scanButton = document.getElementById('scan-button');

  const camera = document.getElementById('camera');
  const canvas = document.getElementById('snapshot');
  const confirmationIcon = document.getElementById('confirmation-icon');
  const confirmationMessage = document.getElementById('confirmation-message');
  const confirmationDetails = document.getElementById('confirmation-details');
  const scanStatus = document.getElementById('scan-status');
  let officeId = document.getElementById("office_id").value;

  // Clock
  function updateTime() {
    const now = new Date();
    clockElement.textContent = now.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit', hour12: true });
    dateElement.textContent = now.toLocaleDateString('en-AU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }
  setInterval(updateTime, 1000); 
  updateTime();

  // Start camera
  function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => { camera.srcObject = stream; })
      .catch(err => { scanStatus.textContent = "Camera access denied"; });
  }

  let isScanning = false;

  // Capture multiple snapshots and send
  function captureMultipleAndSend(numShots = 3, delay = 1000) {
    if (isScanning) return;
    isScanning = true;

    let shots = [];
    let count = 0;

    scanStatus.textContent = `Capturing ${numShots} snapshots...`;

    function takeShot() {
      const ctx = canvas.getContext('2d');
      canvas.width = camera.videoWidth;
      canvas.height = camera.videoHeight;
      ctx.drawImage(camera, 0, 0);
      const dataURL = canvas.toDataURL('image/jpeg');
      shots.push(dataURL);

      count++;
      if (count < numShots) {
        scanStatus.textContent = `Captured ${count}, taking next...`;
        setTimeout(takeShot, delay); // wait before next shot
      } else {
        scanStatus.textContent = "Processing...";

        frappe.call({
          method: 'hex_face.api.recognized_faces',
          args: { images: shots, office_id: officeId },
          callback: function (r) {
            scanScreen.classList.add('hidden');
            confirmationScreen.classList.remove('hidden');

            const clockInTime = new Date().toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });

            if (r.message && r.message.status === "success") {
              confirmationIcon.textContent = '✔️';
              confirmationIcon.style.color = '#28a745';
              confirmationMessage.textContent = `Welcome, ${r.message.name}!`;
              confirmationDetails.textContent = `You have successfully clocked in at ${clockInTime}.`;
            } else {
              confirmationIcon.textContent = '❌';
              confirmationIcon.style.color = '#dc3545';
              confirmationMessage.textContent = 'Authentication Failed';
              confirmationDetails.textContent = (r.message && r.message.reason);
            }

            setTimeout(() => {
              confirmationScreen.classList.add('hidden');
              welcomeScreen.classList.remove('hidden');
              isScanning = false;
            }, 4000);
          }
        });
      }
    }

    takeShot();
  }

  // Button click
  scanButton.addEventListener('click', () => {
    welcomeScreen.classList.add('hidden');
    scanScreen.classList.remove('hidden');
    startCamera();

    // Give 3 seconds to align face, then capture 3 shots with 1s gap
    scanStatus.textContent = "Align your face...";
    setTimeout(() => captureMultipleAndSend(3, 1000), 3000);
  });
});
