function handleChange() {
    fetchData();
    checkDraft();
}

document.addEventListener("DOMContentLoaded", function () {

    let chartTypeEl = document.getElementById("chartType");
    let fileInput = document.getElementById("signed_copy");
    let yearEl = document.getElementById("year");

    if (chartTypeEl) {
        chartTypeEl.addEventListener("change", drawBudgetChart);
    }

    if (fileInput) {
        fileInput.addEventListener("change", function () {
            let file = this.files[0];
            let fileNameEl = document.getElementById("fileName");
            if (fileNameEl) {
                fileNameEl.innerText = file ? "Selected: " + file.name : "";
            }
        });
    }

    document.querySelectorAll("input[type='number']").forEach(function (input) {
        input.addEventListener("input", calculateAll);
    });

    // 🔥 FINAL FIX HERE
    if (yearEl) {
        yearEl.addEventListener("change", function () {

            let state = document.getElementById("state_hidden").value;
            let year = this.value;

            console.log("FETCH TRIGGER:", state, year);

            if (state && year) {
                fetchData();   // 🔥 direct call
            }
        });
    }

});



// ===== HELPER FUNCTIONS =====

function getVal(id) {
    return parseFloat(document.getElementById(id)?.value) || 0;
}

function setVal(id, val) {
    let el = document.getElementById(id);
    if (el) el.value = (parseFloat(val) || 0).toFixed(3);
}

// ===== CLEAR OLD DATA =====

function clearFields() {
    let ids = [
        "ref_r1","ref_r2","ref_r3","ref_r4","ref_r5","ref_r6",
        "saap_r1","saap_r2","saap_r3","saap_r4","saap_r5","saap_r6",
        "md_r1","md_r2","md_r3","md_r4","md_r5","md_r6",
        "b_c_rel_r","b_c_rel_nr","b_s_rel_r","b_s_rel_nr"
    ];

    ids.forEach(id => {
        let el = document.getElementById(id);
        if (el) el.value = "";
    });
}


// ===== MAIN CALCULATION =====

function calculateAll() {

    // ===== COLUMN TOTAL =====

    // Central
    let ct1 = getVal("c1")+getVal("c11")+getVal("c21")+getVal("c31")+getVal("c41")+getVal("c51");
    let ct2 = getVal("c2")+getVal("c12")+getVal("c22")+getVal("c32")+getVal("c42")+getVal("c52");
    let ct3 = getVal("c3")+getVal("c13")+getVal("c23")+getVal("c33")+getVal("c43")+getVal("c53");
    let ct4 = getVal("c4")+getVal("c14")+getVal("c24")+getVal("c34")+getVal("c44")+getVal("c54");

    // State
    let ct5 = getVal("s1")+getVal("s11")+getVal("s21")+getVal("s31")+getVal("s41")+getVal("s51");
    let ct6 = getVal("s2")+getVal("s12")+getVal("s22")+getVal("s32")+getVal("s42")+getVal("s52");
    let ct7 = getVal("s3")+getVal("s13")+getVal("s23")+getVal("s33")+getVal("s43")+getVal("s53");
    let ct8 = getVal("s4")+getVal("s14")+getVal("s24")+getVal("s34")+getVal("s44")+getVal("s54");

    setVal("ct1", ct1);
    setVal("ct2", ct2);
    setVal("ct3", ct3);
    setVal("ct4", ct4);

    setVal("ct5", ct5);
    setVal("ct6", ct6);
    setVal("ct7", ct7);
    setVal("ct8", ct8);

    // ===== COMPONENT TOTAL =====
	// Row 1
	setVal("t1", getVal("c1") + getVal("c2") + getVal("s1") + getVal("s2"));
	setVal("t2", getVal("c3") + getVal("c4") + getVal("s3") + getVal("s4"));

	// Row 2
	setVal("t11", getVal("c11") + getVal("c12") + getVal("s11") + getVal("s12"));
	setVal("t12", getVal("c13") + getVal("c14") + getVal("s13") + getVal("s14"));

	// Row 3
	setVal("t21", getVal("c21") + getVal("c22") + getVal("s21") + getVal("s22"));
	setVal("t22", getVal("c23") + getVal("c24") + getVal("s23") + getVal("s24"));

	// Row 4
	setVal("t31", getVal("c31") + getVal("c32") + getVal("s31") + getVal("s32"));
	setVal("t32", getVal("c33") + getVal("c34") + getVal("s33") + getVal("s34"));

	// Row 5
	setVal("t41", getVal("c41") + getVal("c42") + getVal("s41") + getVal("s42"));
	setVal("t42", getVal("c43") + getVal("c44") + getVal("s43") + getVal("s44"));

	// Row 6
	setVal("t51", getVal("c51") + getVal("c52") + getVal("s51") + getVal("s52"));
	setVal("t52", getVal("c53") + getVal("c54") + getVal("s53") + getVal("s54"));
    // ===== FINAL TOTAL =====
	
	let totalRec = ct1 + ct5;
	let totalNonRec = ct2 + ct6;
	let totalUtil = totalRec + totalNonRec;

	let totalRefRec = ct3 + ct7;
	let totalRefNonRec = ct4 + ct8;

	let totalRefund = totalRefRec + totalRefNonRec;

	setVal("ct9", totalUtil);
	setVal("ct10", totalRefund);
		
// ===== STEP 1: SET VALUES FROM COMPONENT =====

	// Utilization
	setVal("b_c_util_r", ct1);
	setVal("b_c_util_nr", ct2);
	setVal("b_s_util_r", ct5);
	setVal("b_s_util_nr", ct6);

	// Refund
	setVal("b_c_ref_r", ct3);
	setVal("b_c_ref_nr", ct4);
	setVal("b_s_ref_r", ct7);
	setVal("b_s_ref_nr", ct8);


	// ===== STEP 2: ROW TOTAL (Recurring / NonRecurring) =====

	// Util
	setVal("b_t_util_r", getVal("b_c_util_r") + getVal("b_s_util_r"));
	setVal("b_t_util_nr", getVal("b_c_util_nr") + getVal("b_s_util_nr"));

	// Refund
	setVal("b_t_ref_r", getVal("b_c_ref_r") + getVal("b_s_ref_r"));
	setVal("b_t_ref_nr", getVal("b_c_ref_nr") + getVal("b_s_ref_nr"));


	// ===== STEP 3: TOTAL ROW (BOTTOM - Row 3) =====

	// ===== TOTAL ROW (ROW 3) =====

	// Central
	setVal("gt_c_rel", getVal("b_c_rel_r") + getVal("b_c_rel_nr"));
	setVal("gt_c_util", getVal("b_c_util_r") + getVal("b_c_util_nr"));
	setVal("gt_c_ref", getVal("b_c_ref_r") + getVal("b_c_ref_nr"));

	// State
	setVal("gt_s_rel", getVal("b_s_rel_r") + getVal("b_s_rel_nr"));
	setVal("gt_s_util", getVal("b_s_util_r") + getVal("b_s_util_nr"));
	setVal("gt_s_ref", getVal("b_s_ref_r") + getVal("b_s_ref_nr"));

	// Total Column
	setVal("gt_t_rel", getVal("b_t_rel_r") + getVal("b_t_rel_nr"));
	setVal("gt_t_util", getVal("b_t_util_r") + getVal("b_t_util_nr"));
	setVal("gt_t_ref", getVal("b_t_ref_r") + getVal("b_t_ref_nr"));



	// ===== STEP 4: REMAINING =====

	// Recurring
	setVal("b_rem_r",
		getVal("b_t_rel_r") - (getVal("b_t_util_r") + getVal("b_t_ref_r"))
	);

	// Non-Recurring
	setVal("b_rem_nr",
		getVal("b_t_rel_nr") - (getVal("b_t_util_nr") + getVal("b_t_ref_nr"))
	);

	// Total Remaining
	setVal("gt_rem",
    getVal("gt_t_rel") - (getVal("gt_t_util") + getVal("gt_t_ref"))
	);
	
	setVal("gt_rem",
    getVal("b_rem_r") + getVal("b_rem_nr")
);

    // ===== VALIDATION FUNCTION =====
// ===== VALIDATION =====

// Central Recurring
if (getVal("b_c_util_r") + getVal("b_c_ref_r") > getVal("b_c_rel_r")) {
    alert("Central Recurring: Utilization + Refund cannot exceed Released");
    return;
}

// Central Non-Recurring
if (getVal("b_c_util_nr") + getVal("b_c_ref_nr") > getVal("b_c_rel_nr")) {
    alert("Central Non-Recurring: Utilization + Refund cannot exceed Released");
    return;
}

// State Recurring
if (getVal("b_s_util_r") + getVal("b_s_ref_r") > getVal("b_s_rel_r")) {
    alert("State Recurring: Utilization + Refund cannot exceed Released");
    return;
}

// State Non-Recurring
if (getVal("b_s_util_nr") + getVal("b_s_ref_nr") > getVal("b_s_rel_nr")) {
    alert("State Non-Recurring: Utilization + Refund cannot exceed Released");
    return;
}



    // ===== SET REFUND FIRST =====
    setVal("b_c_ref_r", ct3);
    setVal("b_s_ref_r", ct7);
    setVal("b_t_ref_r", getVal("b_c_ref_r") + getVal("b_s_ref_r"));

    setVal("b_c_ref_nr", ct4);
    setVal("b_s_ref_nr", ct8);
    setVal("b_t_ref_nr", getVal("b_c_ref_nr") + getVal("b_s_ref_nr"));

    // ===== VALIDATION + UTILIZATION =====

    if (!validateUtilization(ct1, getVal("b_c_rel_r"), ct3, "Central Recurring")) return;
    setVal("b_c_util_r", ct1);

    if (!validateUtilization(ct2, getVal("b_c_rel_nr"), ct4, "Central Non-Recurring")) return;
    setVal("b_c_util_nr", ct2);

    if (!validateUtilization(ct5, getVal("b_s_rel_r"), ct7, "State Recurring")) return;
    setVal("b_s_util_r", ct5);

    if (!validateUtilization(ct6, getVal("b_s_rel_nr"), ct8, "State Non-Recurring")) return;
    setVal("b_s_util_nr", ct6);

    if (!validateUtilization(totalRec, getVal("b_t_rel_r"), totalRefRec, "Total Recurring")) return;
    setVal("b_t_util_r", getVal("b_c_util_r") + getVal("b_s_util_r"));

    if (!validateUtilization(totalNonRec, getVal("b_t_rel_nr"), totalRefNonRec, "Total Non-Recurring")) return;
    setVal("b_t_util_nr", getVal("b_c_util_nr") + getVal("b_s_util_nr"));

    // ===== REMAINING (CORRECT) =====
    setVal("b_rem_r", getVal("b_t_rel_r") - (getVal("b_t_util_r") + getVal("b_t_ref_r")));
    setVal("b_rem_nr", getVal("b_t_rel_nr") - (getVal("b_t_util_nr") + getVal("b_t_ref_nr")));

    // ===== GRAND TOTAL =====
    let gt_c_rel = getVal("b_c_rel_r") + getVal("b_c_rel_nr");
    let gt_c_util = getVal("b_c_util_r") + getVal("b_c_util_nr");
    let gt_c_ref = getVal("b_c_ref_r") + getVal("b_c_ref_nr");

    let gt_s_rel = getVal("b_s_rel_r") + getVal("b_s_rel_nr");
    let gt_s_util = getVal("b_s_util_r") + getVal("b_s_util_nr");
    let gt_s_ref = getVal("b_s_ref_r") + getVal("b_s_ref_nr");

    let gt_t_rel = getVal("b_t_rel_r") + getVal("b_t_rel_nr");
    let gt_t_util = getVal("b_t_util_r") + getVal("b_t_util_nr");
    let gt_t_ref = getVal("b_t_ref_r") + getVal("b_t_ref_nr");

    let gt_rem = gt_t_rel - (gt_t_util + gt_t_ref);

    setVal("gt_c_rel", gt_c_rel);
    setVal("gt_c_util", gt_c_util);
    setVal("gt_c_ref", gt_c_ref);

    setVal("gt_s_rel", gt_s_rel);
    setVal("gt_s_util", gt_s_util);
    setVal("gt_s_ref", gt_s_ref);

    setVal("gt_t_rel", gt_t_rel);
    setVal("gt_t_util", gt_t_util);
    setVal("gt_t_ref", gt_t_ref);

    setVal("gt_rem", gt_rem);

    // charts
    drawChart();
    drawBudgetChart();
}




function drawChart() {
	
	if (window.myChart && typeof window.myChart.destroy === "function") {
    window.myChart.destroy();
}
    const canvas = document.getElementById("myChart");
	if (!canvas) return;

	const ctx = canvas.getContext("2d");

    window.myChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: [
                "Central Rec",
                "Central NonRec",
                "State Rec",
                "State NonRec",
                "Total Rec",
                "Total NonRec"
            ],
            datasets: [{
                label: "Utilization",
                data: [
                    getVal("b_c_util_r"),
                    getVal("b_c_util_nr"),
                    getVal("b_s_util_r"),
                    getVal("b_s_util_nr"),
                    getVal("b_t_util_r"),
                    getVal("b_t_util_nr")
                ],
                backgroundColor: [
                    "#ff6384",
                    "#36a2eb",
                    "#ffcd56",
                    "#4bc0c0",
                    "#9966ff",
                    "#ff9f40"
                ]
            }]
        }
    });
}

function drawBudgetChart() {

    // ✅ Safe destroy (FIXED)
    if (window.budgetChart && typeof window.budgetChart.destroy === "function") {
        window.budgetChart.destroy();
    }

    const canvas = document.getElementById("budgetChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const chartType = document.getElementById("chartType")?.value || "bar";

    window.budgetChart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: [
                "Ayush Services",
                "Education Institutions",
                "Medicinal Plants",
                "Quality Control of ASU & H Drugs",
                "Flexi Pool",
                "Admin Cost"
            ],
            datasets: [
                {
                    label: "Utilization",
                    data: [
                        getVal("c1")+getVal("c2")+getVal("s1")+getVal("s2"),
                        getVal("c11")+getVal("c12")+getVal("s11")+getVal("s12"),
                        getVal("c21")+getVal("c22")+getVal("s21")+getVal("s22"),
                        getVal("c31")+getVal("c32")+getVal("s31")+getVal("s32"),
                        getVal("c41")+getVal("c42")+getVal("s41")+getVal("s42"),
                        getVal("c51")+getVal("c52")+getVal("s51")+getVal("s52")
                    ],
                    backgroundColor: "#36a2eb"
                },
                {
                    label: "Refund",
                    data: [
                        getVal("c3")+getVal("c4")+getVal("s3")+getVal("s4"),
                        getVal("c13")+getVal("c14")+getVal("s13")+getVal("s14"),
                        getVal("c23")+getVal("c24")+getVal("s23")+getVal("s24"),
                        getVal("c33")+getVal("c34")+getVal("s33")+getVal("s34"),
                        getVal("c43")+getVal("c44")+getVal("s43")+getVal("s44"),
                        getVal("c53")+getVal("c54")+getVal("s53")+getVal("s54")
                    ],
                    backgroundColor: "#ff6384"
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: "Component-wise Utilization vs Refund (Rs. in Lakhs)"
                }
            }
        }
    });
}
