import math
from flask import Flask, request, render_template_string

app = Flask(__name__)

def get_xu_max_ratio(fy):
    if abs(fy - 250.0) < 1.0:
        return 0.53
    elif abs(fy - 415.0) < 1.0:
        return 0.48
    elif abs(fy - 500.0) < 1.0:
        return 0.46
    else:
        return 0.0035 / (0.0055 + 0.87 * fy / 200000.0)

def get_fsc(fy, d_dash_ratio):
    ratios = [0.05, 0.10, 0.15, 0.20]
    if abs(fy - 250.0) < 1.0:
        return 0.87 * 250.0
    elif abs(fy - 415.0) < 1.0:
        fsc_vals = [355.0, 353.0, 342.0, 329.0]
    elif abs(fy - 500.0) < 1.0:
        fsc_vals = [424.0, 412.0, 395.0, 370.0]
    else:
        return 0.87 * fy * (1.0 - d_dash_ratio)

    if d_dash_ratio <= ratios[0]:
        return fsc_vals[0]
    if d_dash_ratio >= ratios[-1]:
        return fsc_vals[-1]

    for i in range(len(ratios) - 1):
        if ratios[i] <= d_dash_ratio <= ratios[i + 1]:
            x0, x1 = ratios[i], ratios[i + 1]
            y0, y1 = fsc_vals[i], fsc_vals[i + 1]
            return y0 + (y1 - y0) * (d_dash_ratio - x0) / (x1 - x0)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="gu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doubly Reinforced Beam 3D Design</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-light: #2563eb;
            --bg: #f8fafc;
            --surface: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --danger: #dc2626;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background-color: var(--bg); color: var(--text-main); padding: 12px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
            color: white; padding: 16px; border-radius: 12px; margin-bottom: 16px;
        }
        .header h1 { font-size: 1.3rem; font-weight: 700; }
        .layout-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
        @media(min-width: 850px) { .layout-grid { grid-template-columns: 1fr 1.2fr; } }
        .card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 1rem; font-weight: 700; color: var(--primary);
            margin-bottom: 12px; padding-bottom: 6px; border-bottom: 2px solid var(--border);
        }
        .form-group { margin-bottom: 10px; }
        .form-group label { display: block; font-size: 0.78rem; font-weight: 600; margin-bottom: 3px; }
        .input-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        input, select {
            width: 100%; padding: 8px 10px; border: 1.5px solid var(--border);
            border-radius: 6px; font-size: 0.85rem; outline: none;
        }
        .btn-submit {
            width: 100%; background: var(--primary); color: white;
            font-size: 0.95rem; font-weight: 600; padding: 11px;
            border: none; border-radius: 6px; cursor: pointer; margin-top: 6px;
        }
        .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
        .metric-box {
            background: #f1f5f9; padding: 8px 10px; border-radius: 6px;
            border-left: 4px solid var(--primary-light);
        }
        .metric-label { font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
        .metric-val { font-size: 1.05rem; font-weight: 700; color: var(--text-main); margin-top: 2px; }
        .detail-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed var(--border); font-size: 0.83rem; }

        #canvas3d-container {
            width: 100%; height: 350px; border-radius: 8px; background: #0b1329;
            position: relative; overflow: hidden; margin-top: 10px;
        }
        
        #canvas3d-container.fullscreen {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 999999 !important;
            border-radius: 0 !important;
            margin: 0 !important;
        }

        .controls-toolbar {
            position: absolute; top: 12px; right: 12px; z-index: 100;
            display: flex; gap: 8px;
        }

        .canvas-btn {
            background: #1e293b; color: #fff; border: 1px solid #475569;
            padding: 7px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .canvas-btn:hover { background: #2563eb; }

        .canvas-hint {
            position: absolute; bottom: 8px; left: 8px; color: #cbd5e1;
            font-size: 0.72rem; background: rgba(15, 23, 42, 0.75); padding: 4px 8px; border-radius: 4px; pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RCC Doubly Reinforced Beam - 3D Visualizer</h1>
            <p style="font-size:0.8rem; opacity:0.9;">Limit State Method (IS 456:2000)</p>
        </div>

        <div class="layout-grid">
            <div class="card">
                <div class="card-title">Design Inputs</div>
                <form method="POST">
                    <div class="input-row">
                        <div class="form-group"><label>Width b (mm)</label><input type="number" step="any" name="b" value="{{ inputs.b }}" required></div>
                        <div class="form-group"><label>Depth D (mm)</label><input type="number" step="any" name="D" value="{{ inputs.D }}" required></div>
                    </div>
                    <div class="input-row">
                        <div class="form-group"><label>Span L (m)</label><input type="number" step="any" name="L" value="{{ inputs.L }}" required></div>
                        <div class="form-group"><label>Live Load (kN/m)</label><input type="number" step="any" name="LL" value="{{ inputs.LL }}" required></div>
                    </div>
                    <div class="form-group">
                        <label style="color:#b91c1c;">Direct Moment Mu (kN·m) [Optional]</label>
                        <input type="number" step="any" name="custom_Mu" placeholder="દા.ત. 160" value="{{ inputs.custom_Mu }}">
                    </div>
                    <div class="input-row">
                        <div class="form-group"><label>fck</label>
                            <select name="fck">
                                <option value="20" {% if inputs.fck == 20 %}selected{% endif %}>M20</option>
                                <option value="25" {% if inputs.fck == 25 %}selected{% endif %}>M25</option>
                                <option value="30" {% if inputs.fck == 30 %}selected{% endif %}>M30</option>
                            </select>
                        </div>
                        <div class="form-group"><label>fy</label>
                            <select name="fy">
                                <option value="415" {% if inputs.fy == 415 %}selected{% endif %}>Fe 415</option>
                                <option value="500" {% if inputs.fy == 500 %}selected{% endif %}>Fe 500</option>
                                <option value="250" {% if inputs.fy == 250 %}selected{% endif %}>Fe 250</option>
                            </select>
                        </div>
                    </div>
                    <div class="input-row">
                        <div class="form-group"><label>Tension Cover d (mm)</label><input type="number" step="any" name="cover_t" value="{{ inputs.cover_t }}" required></div>
                        <div class="form-group"><label>Comp. Cover d' (mm)</label><input type="number" step="any" name="d_dash" value="{{ inputs.d_dash }}" required></div>
                    </div>
                    <div class="input-row">
                        <div class="form-group"><label>Tension Dia (mm)</label><input type="number" step="any" name="dia_t" value="{{ inputs.dia_t }}" required></div>
                        <div class="form-group"><label>Comp. Dia (mm)</label><input type="number" step="any" name="dia_c" value="{{ inputs.dia_c }}" required></div>
                    </div>
                    <button type="submit" class="btn-submit">Calculate &amp; Render 3D</button>
                </form>
            </div>

            <div class="card">
                <div class="card-title">Design Summary &amp; 3D Model</div>
                {% if res %}
                <div class="metric-grid">
                    <div class="metric-box">
                        <div class="metric-label">Design Moment Mu</div>
                        <div class="metric-val">{{ "%.2f"|format(res.Mu) }} <span style="font-size:0.7rem;">kN·m</span></div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Limiting Moment Mu,lim</div>
                        <div class="metric-val">{{ "%.2f"|format(res.Mu_lim) }} <span style="font-size:0.7rem;">kN·m</span></div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Tension Steel</div>
                        <div class="metric-val">{{ "%.1f"|format(res.Ast_total) }} <span style="font-size:0.7rem;">mm²</span></div>
                    </div>
                    <div class="metric-box" style="border-left-color: var(--danger);">
                        <div class="metric-label">Comp. Steel (Asc)</div>
                        <div class="metric-val" style="color:#b91c1c;">{{ "%.1f"|format(res.Asc_req) }} <span style="font-size:0.7rem;">mm²</span></div>
                    </div>
                </div>

                <div class="detail-row">
                    <span>Bottom Reinforcement:</span>
                    <strong>{{ res.num_bars_t }} Nos of {{ inputs.dia_t|int }} mm Dia</strong>
                </div>
                <div class="detail-row">
                    <span>Top Reinforcement (Asc):</span>
                    <strong style="color:#b91c1c;">{{ res.num_bars_c }} Nos of {{ inputs.dia_c|int }} mm Dia</strong>
                </div>

                <div id="canvas3d-container">
                    <div class="controls-toolbar">
                        <button type="button" class="canvas-btn" onclick="resetView()">⟲ Reset View</button>
                        <button type="button" class="canvas-btn" id="toggleFsBtn" onclick="toggleScreen()">⛶ Maximize</button>
                    </div>
                    <div class="canvas-hint">Touch &amp; Drag to Rotate | Pinch to Zoom</div>
                </div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:6px; text-align:center;">
                    <span style="color:#3b82f6;">■</span> Tension Steel &nbsp;|&nbsp; 
                    <span style="color:#ef4444;">■</span> Compression Steel &nbsp;|&nbsp;
                    <span style="color:#94a3b8;">□</span> Stirrups
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    {% if res %}
    <script>
        const container = document.getElementById('canvas3d-container');
        const fsBtn = document.getElementById('toggleFsBtn');

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a1020);

        // Clipping range 0.1 to 10000 ensures no clipping or disappearing on zoom out
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 10000);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.target.set(0, 0, 0); // Always rotate around center of beam
        controls.maxDistance = 5000;  // Prevent infinite zoom-out
        controls.minDistance = 50;

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(500, 800, 600);
        scene.add(dirLight);

        // Parameters
        const b = {{ inputs.b }};
        const D = {{ inputs.D }};
        const length = 600;
        const cover_t = {{ inputs.cover_t }};
        const d_dash = {{ inputs.d_dash }};
        const num_c = {{ res.num_bars_c }};
        const num_t = {{ res.num_bars_t }};
        const dia_c = {{ inputs.dia_c }};
        const dia_t = {{ inputs.dia_t }};

        // 1. Concrete Box (Center origin)
        const concreteGeo = new THREE.BoxGeometry(b, D, length);
        const concreteMat = new THREE.MeshStandardMaterial({
            color: 0x94a3b8,
            transparent: true,
            opacity: 0.2,
            roughness: 0.6
        });
        const concrete = new THREE.Mesh(concreteGeo, concreteMat);
        scene.add(concrete);

        const wireframe = new THREE.LineSegments(
            new THREE.EdgesGeometry(concreteGeo),
            new THREE.LineBasicMaterial({ color: 0x64748b, linewidth: 1.5 })
        );
        scene.add(wireframe);

        // Materials
        const steelMatTop = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.2, metalness: 0.8 });
        const steelMatBottom = new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.2, metalness: 0.8 });

        function addBar(dia, x, y, mat) {
            const barGeo = new THREE.CylinderGeometry(dia / 2, dia / 2, length - 20, 16);
            const bar = new THREE.Mesh(barGeo, mat);
            bar.rotation.x = Math.PI / 2;
            bar.position.set(x, y, 0);
            scene.add(bar);
        }

        // 2. Compression Bars
        const y_top = (D / 2) - d_dash;
        const x_span_top = b - 2 * d_dash;
        for(let i = 0; i < num_c; i++) {
            const x = (num_c > 1) ? (-x_span_top / 2 + (x_span_top / (num_c - 1)) * i) : 0;
            addBar(dia_c, x, y_top, steelMatTop);
        }

        // 3. Tension Bars
        const y_bot = -(D / 2) + cover_t;
        const x_span_bot = b - 2 * cover_t;
        for(let i = 0; i < num_t; i++) {
            const x = (num_t > 1) ? (-x_span_bot / 2 + (x_span_bot / (num_t - 1)) * i) : 0;
            addBar(dia_t, x, y_bot, steelMatBottom);
        }

        // 4. Closed Stirrups (Complete 4-sided loop)
        const stirrupMat = new THREE.LineBasicMaterial({ color: 0xe2e8f0, linewidth: 2 });
        const numStirrups = 7;
        for(let i = 0; i < numStirrups; i++) {
            const z = -length / 2 + 40 + (length - 80) / (numStirrups - 1) * i;
            const points = [
                new THREE.Vector3(-b/2 + 20, -D/2 + 20, z),
                new THREE.Vector3(b/2 - 20, -D/2 + 20, z),
                new THREE.Vector3(b/2 - 20, D/2 - 20, z),
                new THREE.Vector3(-b/2 + 20, D/2 - 20, z),
                new THREE.Vector3(-b/2 + 20, -D/2 + 20, z) // Closed loop
            ];
            const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
            scene.add(new THREE.Line(lineGeo, stirrupMat));
        }

        function resetView() {
            camera.position.set(700, 450, 850);
            controls.target.set(0, 0, 0);
            controls.update();
        }
        resetView();

        function updateRendererSize() {
            const w = container.clientWidth;
            const h = container.clientHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }

        function toggleScreen() {
            container.classList.toggle('fullscreen');
            if (container.classList.contains('fullscreen')) {
                fsBtn.innerHTML = "🗗 Minimize";
                document.body.style.overflow = "hidden";
            } else {
                fsBtn.innerHTML = "⛶ Maximize";
                document.body.style.overflow = "auto";
            }
            setTimeout(() => {
                updateRendererSize();
                controls.target.set(0, 0, 0);
            }, 100);
        }

        window.addEventListener('resize', updateRendererSize);

        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        animate();
    </script>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    inputs = {
        "b": 230, "D": 450, "L": 5.0, "cover_t": 40, "d_dash": 40,
        "fck": 20, "fy": 415, "LL": 32.0, "dia_t": 20, "dia_c": 16,
        "custom_Mu": ""
    }
    
    res = None
    if request.method == "POST":
        for k in ["b", "D", "L", "cover_t", "d_dash", "fck", "fy", "LL", "dia_t", "dia_c"]:
            inputs[k] = float(request.form.get(k, inputs[k]))
        inputs["custom_Mu"] = request.form.get("custom_Mu", "").strip()

        b = inputs["b"]
        D = inputs["D"]
        L = inputs["L"]
        cover_t = inputs["cover_t"]
        d_dash = inputs["d_dash"]
        fck = inputs["fck"]
        fy = inputs["fy"]
        LL = inputs["LL"]
        dia_t = inputs["dia_t"]
        dia_c = inputs["dia_c"]

        d = D - cover_t
        
        xu_max_ratio = get_xu_max_ratio(fy)
        xu_max = xu_max_ratio * d
        Mu_lim = (0.36 * fck * b * xu_max * (d - 0.42 * xu_max)) / 1e6
        Ast_lim = (0.36 * fck * b * xu_max) / (0.87 * fy)

        if inputs["custom_Mu"]:
            Mu = float(inputs["custom_Mu"])
        else:
            DL = 25.0 * (b / 1000.0) * (D / 1000.0)
            wu = 1.5 * (DL + LL)
            Mu = (wu * (L ** 2)) / 8.0

        Mu2 = Mu - Mu_lim
        if Mu2 <= 0:
            Mu2 = 0.25 * Mu_lim
            Mu = Mu_lim + Mu2

        d_dash_ratio = d_dash / d
        fsc = get_fsc(fy, d_dash_ratio)
        fcc = 0.446 * fck

        Asc_req = (Mu2 * 1e6) / ((fsc - fcc) * (d - d_dash))
        Ast2 = (Asc_req * (fsc - fcc)) / (0.87 * fy)
        Ast_total = Ast_lim + Ast2

        area_one_t = (math.pi / 4.0) * (dia_t ** 2)
        num_bars_t = max(2, math.ceil(Ast_total / area_one_t))

        area_one_c = (math.pi / 4.0) * (dia_c ** 2)
        num_bars_c = max(2, math.ceil(Asc_req / area_one_c))

        res = {
            "Mu": Mu, "Mu_lim": Mu_lim, "Mu2": Mu2, "fsc": fsc,
            "Ast_total": Ast_total, "Asc_req": Asc_req,
            "num_bars_t": int(num_bars_t), "num_bars_c": int(num_bars_c)
        }

    return render_template_string(HTML_TEMPLATE, inputs=inputs, res=res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
