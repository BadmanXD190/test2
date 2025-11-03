

import streamlit as st

# ========= CONFIGURE YOUR MODEL & DEVICE =========
MODEL_ID = "qeVM1Dsr5"       # <-- replace with your Teachable Machine model ID
DEVICE_ID = "robotcar_umk1" # same as in your ESP code
BROKER_WS = "wss://test.mosquitto.org:8081/mqtt"  # Mosquitto WS port (8081)
TOPIC_CMD = f"rc/{DEVICE_ID}/cmd"
# ================================================

st.set_page_config(page_title="Rebooted Vision Controller", layout="centered")
st.title("🤖 Teachable Machine → ESP32 Robot Car")
st.write("This Streamlit page loads your Teachable Machine model, performs real-time classification in the browser, and sends commands to your ESP32 via MQTT.")

html = f"""
<div style="font-family:system-ui,Segoe UI,Roboto,Arial">
  <button id="start" style="padding:10px 16px;border-radius:10px;">Start Webcam</button>
  <div id="status" style="margin:10px 0;font-weight:600;">Idle</div>
  <video id="webcam" autoplay playsinline width="320" height="240" style="border-radius:12px"></video>
  <div id="label" style="margin-top:12px;font-size:18px;font-weight:600;"></div>
  <div style="margin-top:10px;font-size:12px;opacity:.7;">
    Publishing to <code>{TOPIC_CMD}</code> on <code>{BROKER_WS}</code>
  </div>
</div>

<!-- TensorFlow.js + Teachable Machine -->
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4"></script>
<script src="https://cdn.jsdelivr.net/npm/@teachablemachine/image@0.8/dist/teachablemachine-image.min.js"></script>

<!-- MQTT.js -->
<script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>

<script>
const MODEL_URL = "https://teachablemachine.withgoogle.com/models/{MODEL_ID}/";
const MQTT_URL  = "{BROKER_WS}";
const TOPIC     = "{TOPIC_CMD}";

let model, webcam, maxPredictions;
let mqttClient;
let lastLabel = "";
let lastSent  = 0;
const INTERVAL_MS = 500;

// ===== MQTT connect =====
function mqttConnect() {{
  mqttClient = mqtt.connect(MQTT_URL, {{
    clientId: "tm-client-" + Math.random().toString(16).substr(2, 8),
    clean: true,
    reconnectPeriod: 2000
  }});
  mqttClient.on("connect", () => setStatus("MQTT connected ✔️"));
  mqttClient.on("reconnect", () => setStatus("Reconnecting MQTT..."));
  mqttClient.on("error", err => setStatus("MQTT error: " + err.message));
}}

// ===== TF.js load & webcam loop =====
async function init() {{
  setStatus("Loading model...");
  const modelURL = MODEL_URL + "model.json";
  const metadataURL = MODEL_URL + "metadata.json";
  model = await tmImage.load(modelURL, metadataURL);
  maxPredictions = model.getTotalClasses();

  setStatus("Starting webcam...");
  webcam = new tmImage.Webcam(320, 240, true);
  await webcam.setup();
  await webcam.play();
  document.getElementById("webcam").replaceWith(webcam.canvas);
  setStatus("Running predictions...");
  mqttConnect();
  window.requestAnimationFrame(loop);
}}

async function loop() {{
  webcam.update();
  await predict();
  window.requestAnimationFrame(loop);
}}

async function predict() {{
  const prediction = await model.predict(webcam.canvas);
  prediction.sort((a,b)=>b.probability-a.probability);
  const p = prediction[0];
  const label = p.className;
  const prob  = p.probability.toFixed(3);
  document.getElementById("label").innerText = label + " (" + prob + ")";
  maybePublish(label);
}}

function maybePublish(label) {{
  const now = Date.now();
  if (!mqttClient || !mqttClient.connected) return;
  if (label !== lastLabel || now - lastSent > INTERVAL_MS) {{
    let cmd = mapLabelToCmd(label);
    if (cmd) {{
      mqttClient.publish(TOPIC, cmd);
      setStatus("Sent: " + cmd);
      lastLabel = label;
      lastSent = now;
    }}
  }}
}}

function mapLabelToCmd(label) {{
  // Map your model labels to single-letter robot commands
  label = label.toLowerCase();
  if (label.includes("forward")) return "F";
  if (label.includes("back"))    return "B";
  if (label.includes("left"))    return "L";
  if (label.includes("right"))   return "R";
  if (label.includes("stop"))    return "S";
  return "";
}}

function setStatus(text) {{
  document.getElementById("status").innerText = text;
}}

document.getElementById("start").addEventListener("click", init);
</script>
"""

st.components.v1.html(html, height=520)
