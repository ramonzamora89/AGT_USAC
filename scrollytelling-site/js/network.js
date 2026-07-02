/**
 * Network Visualization Engine (D3.js + Canvas 2D)
 * AGT_USAC Scrollytelling Site
 * Pasos: 0 intro, 1 bots, 2-7 narrativas (Medios + 5 temáticas), 8 bots detalle, 9 top hubs.
 */

const canvas = document.querySelector("#network-canvas");
const ctx = canvas.getContext("2d");
const tooltip = document.querySelector("#tooltip");

let width, height;
let networkData = null;
let filteredNodes = [];
let filteredLinks = [];
let currentTransform = d3.zoomIdentity;
let activeStep = 0;
let activeClusterKey = null;

let nodesById = new Map();

const NARRATIVE_STEP_MIN = 2;
const NARRATIVE_STEP_MAX = 7;
const BOT_STEP = 8;
const HUBS_STEP = 9;

const COLORS = {
    organic: "#4285F4",
    inorganic: "#e74c3c",
    medio: "#eda100",
    muted: "rgba(100, 116, 139, 0.08)",
    mutedLink: "rgba(0, 0, 0, 0.03)",
    activeLink: "rgba(15, 23, 42, 0.14)",
    highlightLink: "rgba(66, 133, 244, 0.3)"
};

function resize() {
    width = canvas.parentElement.clientWidth;
    height = canvas.parentElement.clientHeight;
    canvas.width = width;
    canvas.height = height;
    if (networkData) draw();
}
window.addEventListener("resize", resize);
resize();

const clusterCenters = {};

d3.json("visuals/executive_network.json").then(data => {
    networkData = data;

    // El JSON ya viene recortado a los nodos relevantes (scripts/export_executive_json.py) —
    // no se vuelve a filtrar acá, para no descartar la muestra de cuentas inorgánicas
    // (que suelen tener in-degree bajo).
    filteredNodes = data.nodes;

    const nodeIds = new Set(filteredNodes.map(d => d.id));
    filteredNodes.forEach(node => nodesById.set(node.id, node));

    filteredLinks = data.links.filter(l =>
        (typeof l.source === 'string' ? nodeIds.has(l.source) : nodeIds.has(l.source.id)) &&
        (typeof l.target === 'string' ? nodeIds.has(l.target) : nodeIds.has(l.target.id))
    );

    // distance(40) y charge(-80): layout más compacto = red más legible al nivel global
    const simulation = d3.forceSimulation(filteredNodes)
        .force("link", d3.forceLink(filteredLinks).id(d => d.id).distance(40))
        .force("charge", d3.forceManyBody().strength(-80))
        .force("center", d3.forceCenter(width / 2, height / 2));

    for (let i = 0; i < 300; i++) simulation.tick();
    simulation.stop();

    calculateClusterCenters();
    populateUI();
    resetZoom();
    setupInteractions();
    draw();
}).catch(err => {
    console.error("Error loading network data:", err);
});

function calculateClusterCenters() {
    if (!networkData) return;
    Object.keys(networkData.narratives).forEach(key => {
        const narrative = networkData.narratives[key];
        const actorIds = new Set(narrative.top_actors.map(a => a.id));
        const matchingNodes = filteredNodes.filter(n => actorIds.has(n.id));

        if (matchingNodes.length > 0) {
            const xs = matchingNodes.map(n => n.x);
            const ys = matchingNodes.map(n => n.y);
            clusterCenters[key] = {
                x: d3.mean(matchingNodes, n => n.x),
                y: d3.mean(matchingNodes, n => n.y),
                spanX: Math.max(...xs) - Math.min(...xs),
                spanY: Math.max(...ys) - Math.min(...ys)
            };
        } else {
            clusterCenters[key] = { x: width / 2, y: height / 2, spanX: 200, spanY: 200 };
        }
    });
}

// key de narrativa -> id del contenedor de badges en el HTML
const NARRATIVE_CONTAINERS = {
    Medios: "#actors-medios",
    Decepcion_Traicion_Politica: "#actors-decepcion",
    USAC_Fraude_Rectoria: "#actors-usac",
    Pactos_y_Corrupcion: "#actors-pactos",
    Ana_Glenda_Tager: "#actors-tager",
    Plan_Infraestructura_Quinonez: "#actors-infra"
};

function populateUI() {
    if (!networkData) return;

    const botGrid = document.querySelector("#bot-grid");
    if (botGrid) {
        botGrid.innerHTML = "";
        networkData.stats.all_bots.slice(0, 32).forEach(bot => {
            const badge = document.createElement("span");
            badge.className = "actor-badge inorganic";
            badge.innerText = `@${bot}`;
            botGrid.appendChild(badge);
        });
    }

    Object.keys(NARRATIVE_CONTAINERS).forEach(key => {
        const container = document.querySelector(NARRATIVE_CONTAINERS[key]);
        if (container && networkData.narratives[key]) {
            container.innerHTML = "";
            networkData.narratives[key].top_actors.forEach(actor => {
                const badge = document.createElement("span");
                badge.className = `actor-badge ${actor.type}`;
                badge.innerText = `@${actor.id}`;
                container.appendChild(badge);
            });
        }
    });
}

function draw() {
    if (!networkData) return;

    ctx.save();
    ctx.clearRect(0, 0, width, height);
    ctx.translate(currentTransform.x, currentTransform.y);
    ctx.scale(currentTransform.k, currentTransform.k);

    filteredLinks.forEach(link => {
        const source = nodesById.get(link.source.id || link.source);
        const target = nodesById.get(link.target.id || link.target);
        if (!source || !target) return;

        ctx.beginPath();

        if (activeStep === 0 || activeStep === 1) {
            ctx.strokeStyle = COLORS.activeLink;
            ctx.lineWidth = 0.6 / Math.sqrt(currentTransform.k);
        } else if (activeStep >= NARRATIVE_STEP_MIN && activeStep <= NARRATIVE_STEP_MAX) {
            const narrative = networkData.narratives[activeClusterKey];
            const actorIds = narrative ? new Set(narrative.top_actors.map(a => a.id)) : null;
            if (actorIds && actorIds.has(source.id) && actorIds.has(target.id)) {
                ctx.strokeStyle = COLORS.highlightLink;
                ctx.lineWidth = 1.0 / Math.sqrt(currentTransform.k);
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        } else if (activeStep === BOT_STEP) {
            if (source.type === 'inorganic' && target.type === 'inorganic') {
                ctx.strokeStyle = "rgba(231, 76, 60, 0.25)";
                ctx.lineWidth = 0.8 / Math.sqrt(currentTransform.k);
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        } else if (activeStep === HUBS_STEP) {
            if (source.label || target.label) {
                ctx.strokeStyle = "rgba(66, 133, 244, 0.35)";
                ctx.lineWidth = 0.8 / Math.sqrt(currentTransform.k);
            } else {
                ctx.strokeStyle = COLORS.mutedLink;
                ctx.lineWidth = 0.2 / Math.sqrt(currentTransform.k);
            }
        }

        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
    });

    filteredNodes.forEach(node => {
        ctx.beginPath();
        const radius = Math.sqrt(node.val) * 0.65;
        let opacity = 1.0;
        let color = node.es_medio ? COLORS.medio : (node.type === 'inorganic' ? COLORS.inorganic : COLORS.organic);

        if (activeStep === 0 || activeStep === 1) {
            opacity = 1.0;
        } else if (activeStep >= NARRATIVE_STEP_MIN && activeStep <= NARRATIVE_STEP_MAX) {
            const narrative = networkData.narratives[activeClusterKey];
            const actorIds = narrative ? new Set(narrative.top_actors.map(a => a.id)) : null;
            if (actorIds && actorIds.has(node.id)) {
                opacity = 1.0;
                ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(66, 133, 244, 0.15)";
                ctx.fill();
                ctx.beginPath();
            } else {
                opacity = 0.08;
            }
        } else if (activeStep === BOT_STEP) {
            if (node.type === 'inorganic') {
                opacity = 1.0;
                color = COLORS.inorganic;
                ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(231, 76, 60, 0.15)";
                ctx.fill();
                ctx.beginPath();
            } else {
                opacity = 0.08;
            }
        } else if (activeStep === HUBS_STEP) {
            if (node.label) {
                opacity = 1.0;
                ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(0, 0, 0, 0.03)";
                ctx.fill();
                ctx.beginPath();
            } else {
                opacity = 0.08;
            }
        }

        ctx.fillStyle = hexToRgba(color, opacity);
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fill();
    });

    filteredNodes.forEach(node => {
        if (node.label) {
            let showLabel = false;
            let labelColor = "#2c3e50";
            let opacity = 1.0;

            if (activeStep === 0 || activeStep === 1) {
                showLabel = true; // con red compacta el zoom inicial ya es suficiente para leer
                opacity = 0.75;
            } else if (activeStep >= NARRATIVE_STEP_MIN && activeStep <= NARRATIVE_STEP_MAX) {
                const narrative = networkData.narratives[activeClusterKey];
                const actorIds = narrative ? new Set(narrative.top_actors.map(a => a.id)) : null;
                showLabel = !!(actorIds && actorIds.has(node.id));
                labelColor = node.es_medio ? "#92620a" : "#1e40af";
            } else if (activeStep === BOT_STEP) {
                showLabel = node.type === 'inorganic' && node.val > 3;
                labelColor = "#991b1b";
            } else if (activeStep === HUBS_STEP) {
                showLabel = true;
                labelColor = node.type === 'inorganic' ? "#991b1b" : "#1e40af";
            }

            if (showLabel) {
                const radius = Math.sqrt(node.val) * 0.65;
                ctx.font = `bold ${10 / Math.sqrt(currentTransform.k) + 8}px 'Poppins', sans-serif`;
                ctx.fillStyle = hexToRgba(labelColor, opacity);
                ctx.fillText(node.label, node.x + radius + 3, node.y + 3);
            }
        }
    });

    ctx.restore();
}

function hexToRgba(hex, alpha) {
    let r = 0, g = 0, b = 0;
    if (hex.startsWith("#")) {
        if (hex.length === 4) {
            r = parseInt(hex[1] + hex[1], 16);
            g = parseInt(hex[2] + hex[2], 16);
            b = parseInt(hex[3] + hex[3], 16);
        } else if (hex.length === 7) {
            r = parseInt(hex.substring(1, 3), 16);
            g = parseInt(hex.substring(3, 5), 16);
            b = parseInt(hex.substring(5, 7), 16);
        }
    } else if (hex.startsWith("rgba")) {
        return hex;
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function transitionTo(targetX, targetY, targetScale) {
    const x = width / 2 - targetX * targetScale;
    const y = height / 2 - targetY * targetScale;

    const interpolator = d3.interpolate(
        { x: currentTransform.x, y: currentTransform.y, k: currentTransform.k },
        { x, y, k: targetScale }
    );

    d3.transition()
        .duration(1100)
        .ease(d3.easeCubicInOut)
        .tween("zoom", () => (t) => {
            const current = interpolator(t);
            currentTransform = d3.zoomIdentity.translate(current.x, current.y).scale(current.k);
            draw();
        });
}

function resetZoom() {
    if (filteredNodes.length === 0) return;
    const minX = d3.min(filteredNodes, d => d.x);
    const maxX = d3.max(filteredNodes, d => d.x);
    const minY = d3.min(filteredNodes, d => d.y);
    const maxY = d3.max(filteredNodes, d => d.y);
    const centerX = d3.mean(filteredNodes, d => d.x);
    const centerY = d3.mean(filteredNodes, d => d.y);

    // Sin tope artificial: la red llena el 90% del canvas según su distribución real
    const scaleX = (width * 0.90) / (maxX - minX);
    const scaleY = (height * 0.90) / (maxY - minY);
    const targetScale = Math.min(scaleX, scaleY);

    currentTransform = d3.zoomIdentity
        .translate(width / 2 - centerX * targetScale, height / 2 - centerY * targetScale)
        .scale(targetScale);
}

function setVisualState(stepIndex, clusterKey) {
    activeStep = stepIndex;
    activeClusterKey = clusterKey;
    if (!networkData) return;

    if (stepIndex === 0 || stepIndex === 1) {
        resetZoom();
        draw();
    } else if (stepIndex >= NARRATIVE_STEP_MIN && stepIndex <= NARRATIVE_STEP_MAX) {
        const center = clusterCenters[clusterKey];
        if (center) {
            // Encuadrar todos los top_actors del clúster con margen cómodo
            const padding = 250;
            const fitScaleX = (center.spanX + padding) > 0 ? (width * 0.80) / (center.spanX + padding) : 2.5;
            const fitScaleY = (center.spanY + padding) > 0 ? (height * 0.80) / (center.spanY + padding) : 2.5;
            // Mínimo 1.5x para siempre acercar respecto a la vista global; máximo 4x
            const targetScale = Math.max(1.5, Math.min(fitScaleX, fitScaleY, 4.0));
            transitionTo(center.x, center.y, targetScale);
        }
    } else if (stepIndex === BOT_STEP) {
        const inorganicNodes = filteredNodes.filter(n => n.type === 'inorganic');
        if (inorganicNodes.length > 0) {
            const avgX = d3.mean(inorganicNodes, n => n.x);
            const avgY = d3.mean(inorganicNodes, n => n.y);
            transitionTo(avgX, avgY, 0.52);
        } else {
            resetZoom();
            draw();
        }
    } else if (stepIndex === HUBS_STEP) {
        const hubs = filteredNodes.filter(n => n.label !== "");
        if (hubs.length > 0) {
            const avgX = d3.mean(hubs, n => n.x);
            const avgY = d3.mean(hubs, n => n.y);
            transitionTo(avgX, avgY, 0.72);
        } else {
            resetZoom();
            draw();
        }
    }
}

function setupInteractions() {
    canvas.addEventListener("mousemove", (event) => {
        if (!networkData || filteredNodes.length === 0) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = (event.clientX - rect.left - currentTransform.x) / currentTransform.k;
        const mouseY = (event.clientY - rect.top - currentTransform.y) / currentTransform.k;

        let hoveredNode = null;
        let minDistance = 15 / currentTransform.k;

        filteredNodes.forEach(node => {
            const dx = node.x - mouseX;
            const dy = node.y - mouseY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < minDistance) {
                minDistance = distance;
                hoveredNode = node;
            }
        });

        if (hoveredNode) {
            const isBot = hoveredNode.type === 'inorganic';
            let roleText = hoveredNode.es_medio
                ? '<span style="color:#92620a;">Medio de comunicación</span>'
                : (isBot ? '<span class="inorganic-text">Inorgánico (Bot)</span>' : '<span class="organic-text">Orgánico</span>');

            tooltip.innerHTML = `
                <strong>@${hoveredNode.id}</strong>
                Rol: ${roleText}<br>
                Centralidad: ${hoveredNode.val.toFixed(1)}<br>
                Comunidad: Clúster #${hoveredNode.group}
            `;

            tooltip.style.opacity = 1;
            const tooltipWidth = tooltip.offsetWidth || 200;
            const tooltipHeight = tooltip.offsetHeight || 90;

            let posX = event.clientX + 15;
            let posY = event.clientY + 15;
            if (posX + tooltipWidth > window.innerWidth) posX = event.clientX - tooltipWidth - 15;
            if (posY + tooltipHeight > window.innerHeight) posY = event.clientY - tooltipHeight - 15;

            tooltip.style.left = `${posX}px`;
            tooltip.style.top = `${posY}px`;
            canvas.style.cursor = "pointer";
        } else {
            tooltip.style.opacity = 0;
            canvas.style.cursor = "default";
        }
    });
}
