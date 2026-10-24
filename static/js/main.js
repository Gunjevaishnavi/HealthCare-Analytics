/**
 * Healthcare Analytics Client-Side Interactivity
 */

// Live Physiological Measurement Range Validator
async function testRangeValidation(event) {
    if (event) event.preventDefault();

    const measureType = document.getElementById("val_measure_type").value;
    const valueInput = document.getElementById("val_value").value;
    const resultBox = document.getElementById("validation_result_box");

    if (!valueInput || isNaN(valueInput)) {
        resultBox.innerHTML = `
            <div class="alert alert-warning py-2 mb-0">
                <i class="bi bi-exclamation-triangle me-1"></i> Please enter a valid numeric measurement value.
            </div>`;
        return;
    }

    resultBox.innerHTML = `<div class="text-muted small"><i class="bi bi-arrow-repeat spin"></i> Validating against documented assumptions...</div>`;

    try {
        const response = await fetch("/api/v1/measurements/validate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                measure_type: measureType,
                value: parseFloat(valueInput)
            })
        });

        const data = await response.json();
        if (!response.ok) {
            resultBox.innerHTML = `<div class="alert alert-danger py-2 mb-0">${data.error || "Validation error"}</div>`;
            return;
        }

        let badgeClass = "bg-success";
        let statusIcon = "bi-check-circle-fill";
        if (data.validation_status === "OUT_OF_RANGE_HIGH") {
            badgeClass = "bg-warning text-dark";
            statusIcon = "bi-arrow-up-circle-fill";
        } else if (data.validation_status === "OUT_OF_RANGE_LOW") {
            badgeClass = "bg-info text-dark";
            statusIcon = "bi-arrow-down-circle-fill";
        } else if (data.validation_status === "IMPLAUSIBLE_VALUE") {
            badgeClass = "bg-danger";
            statusIcon = "bi-x-octagon-fill";
        }

        const assumptions = data.documented_assumptions || {};

        resultBox.innerHTML = `
            <div class="card bg-light border p-3">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="badge ${badgeClass} px-2 py-1 fs-6">
                        <i class="bi ${statusIcon} me-1"></i> ${data.validation_status}
                    </span>
                    <span class="text-muted small">Assumed Unit: <strong>${data.unit}</strong></span>
                </div>
                <div class="fw-semibold mb-1">${data.message}</div>
                <div class="small text-secondary mb-2">
                    Standard Reference Interval: <strong>${assumptions.normal_min ?? 'N/A'} - ${assumptions.normal_max ?? 'N/A'} ${data.unit}</strong> | 
                    Plausible Limits: <strong>[${assumptions.plausible_min ?? 'N/A'}, ${assumptions.plausible_max ?? 'N/A'}]</strong>
                </div>
                <div class="small text-muted border-top pt-2">
                    <i class="bi bi-info-circle me-1"></i> <em>Documented Sample Assumption:</em> ${assumptions.assumption_notes || 'Standard physiological distribution.'}
                </div>
            </div>
        `;
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger py-2 mb-0">Failed to connect: ${err.message}</div>`;
    }
}

// On-demand Patient Indicator Evaluator
async function triggerPatientEvaluation(patientId) {
    if (!confirm(`Evaluate transparent risk indicators for synthetic patient ${patientId}?`)) return;

    try {
        const response = await fetch(`/api/v1/indicators/evaluate/${patientId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": "health-demo-key-2026"
            }
        });

        const data = await response.json();
        if (response.ok) {
            alert(`Evaluation complete for ${patientId}.\nActive Indicators Flagged: ${data.active_indicators_count}\nRules: ${data.triggered_rules.map(r => r.rule_code).join(', ') || 'None'}`);
            window.location.reload();
        } else {
            alert("Error: " + (data.error || "Evaluation failed"));
        }
    } catch (err) {
        alert("Evaluation request failed: " + err.message);
    }
}

// Helper: Quick copy API key
function copyText(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
        setTimeout(() => { btn.innerHTML = orig; }, 1500);
    });
}
