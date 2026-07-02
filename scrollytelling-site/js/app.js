/**
 * Narrative Controller (Intersection Observer Interface)
 * AGT_USAC Scrollytelling Site
 */

document.addEventListener("DOMContentLoaded", () => {
    const steps = document.querySelectorAll(".step");

    const observerOptions = {
        root: null,
        rootMargin: "-25% 0px -35% 0px",
        threshold: 0.15
    };

    let lastActiveStepIndex = -1;

    const stepObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const targetStep = entry.target;
                const stepIndex = parseInt(targetStep.getAttribute("data-step"));
                const clusterKey = targetStep.getAttribute("data-cluster");

                if (stepIndex !== lastActiveStepIndex) {
                    lastActiveStepIndex = stepIndex;

                    steps.forEach(s => s.classList.remove("active"));
                    targetStep.classList.add("active");

                    if (typeof setVisualState === "function") {
                        setVisualState(stepIndex, clusterKey);
                    }

                    updateLegendForStep(stepIndex);
                }
            }
        });
    }, observerOptions);

    steps.forEach(step => stepObserver.observe(step));

    function updateLegendForStep(index) {
        const zoomHint = document.querySelector("#zoom-hint");
        if (!zoomHint) return;

        const hints = {
            0: "Desplázate hacia abajo para ver el desglose",
            1: "Rojo: cuentas inorgánicas coordinadas | Azul: cuentas orgánicas",
            2: "Enfoque: clúster de medios de comunicación",
            3: "Enfoque: decepción y traición política",
            4: "Enfoque: USAC, fraude y crisis de rectoría",
            5: "Enfoque: pactos y corrupción opaca",
            6: "Enfoque: figura de Ana Glenda Tager",
            7: "Enfoque: plan de infraestructura / Ricardo Quiñonez",
            8: "Muestra de perfiles inorgánicos con anomalías topológicas",
            9: "Top 20 perfiles más centrales del debate"
        };

        if (hints[index] !== undefined) {
            zoomHint.innerText = hints[index];
        }
    }
});
