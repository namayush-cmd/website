let headers1 = [];
let headers2 = [];

// =====================
// UPLOAD FILES
// =====================
function uploadFiles() {
    let file1 = document.getElementById('file1').files[0];
    let file2 = document.getElementById('file2').files[0];

    if (!file1 || !file2) {
        alert("Please upload both files");
        return;
    }

    // Show file names
    document.getElementById("file1Name").innerHTML = "📄 " + file1.name;
    document.getElementById("file2Name").innerHTML = "📄 " + file2.name;

    let formData = new FormData();
    formData.append('file1', file1);
    formData.append('file2', file2);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        headers1 = data.headers1;
        headers2 = data.headers2;

        createDynamicMapping();
    });
}

// =====================
// CREATE DYNAMIC ROWS
// =====================
function createDynamicMapping() {
    let area = document.getElementById("mappingArea");
    area.innerHTML = "";

    addRow();

    document.getElementById("mappingSection").style.display = "block";
}

// =====================
// ADD ROW
// =====================
function addRow() {
    let area = document.getElementById("mappingArea");
    let rowId = Date.now();

    let html = `
    <div id="row-${rowId}" style="display:flex; gap:10px; margin-bottom:10px;">

        <!-- Sheet1 Header -->
        <select onchange="loadSubActivities(this,'sub1-${rowId}')" id="h1-${rowId}">
            <option>Select Sheet1 Header</option>
            ${headers1.map(h => `<option value="${h}">${h}</option>`).join("")}
        </select>

        <!-- Sheet1 Activity -->
        <select id="sub1-${rowId}">
            <option>Activity</option>
        </select>

        <!-- Sheet2 Header -->
        <select onchange="loadSubActivities(this,'sub2-${rowId}',2)" id="h2-${rowId}">
            <option>Select Sheet2 Header</option>
            ${headers2.map(h => `<option value="${h}">${h}</option>`).join("")}
        </select>

        <!-- Sheet2 Activity -->
        <select id="sub2-${rowId}">
            <option>Activity</option>
        </select>

        <button onclick="addRow()">➕</button>
        <button onclick="removeRow('${rowId}')">❌</button>
    </div>
    `;

    area.innerHTML += html;
}

// =====================
// REMOVE ROW
// =====================
function removeRow(id) {
    document.getElementById(`row-${id}`).remove();
}

// =====================
// LOAD SUB ACTIVITIES
// =====================
function loadSubActivities(select, targetId, sheet = 1) {
    let header = select.value;

    fetch('/get_values', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ header: header, sheet: sheet })
    })
    .then(res => res.json())
    .then(values => {
        let sub = document.getElementById(targetId);
        sub.innerHTML = "";

        values.forEach(v => {
            sub.innerHTML += `<option value="${v}">${v}</option>`;
        });
    });
}

// =====================
// SUBMIT MAPPING
// =====================
function submitMapping() {
    let rows = document.querySelectorAll(".map-row");

    let mapping = {
        activity1: document.querySelector("[id^='h1-']").value,
        activity2: document.querySelector("[id^='h2-']").value,
        amount1: prompt("Enter Sheet1 Amount Column"),
        amount2: prompt("Enter Sheet2 Amount Column")
    };

    document.getElementById("result").innerHTML = "⏳ Reconciling...";

    fetch('/reconcile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mapping: mapping })
    })
    .then(res => res.json())
    .then(data => {
        showResult(data);
    });
}
document.getElementById("file1").addEventListener("change", function() {
    if (this.files[0]) {
        document.getElementById("file1Text").innerHTML = "📄 " + this.files[0].name;
    }
});

document.getElementById("file2").addEventListener("change", function() {
    if (this.files[0]) {
        document.getElementById("file2Text").innerHTML = "📄 " + this.files[0].name;
    }
});
// =====================
// SHOW RESULT (FINAL)
// =====================
function showResult(data) {
    let html = `
    <h3>📊 Summary</h3>
    <div style="background:#fff;padding:10px;border-radius:8px;margin-bottom:10px;">
        Sheet1 Total: ${data.summary.sheet1_total}<br>
        Sheet2 Total: ${data.summary.sheet2_total}<br>
        Matched Amount: ${data.summary.matched}<br>
        Unmatched Amount: ${data.summary.unmatched}
    </div>
    `;

    html += `
    <table border="1" style="width:100%; border-collapse:collapse;">
    <tr>
        <th>Activity</th>
        <th>Sheet1 Amount</th>
        <th>Sheet2 Amount</th>
        <th>Status</th>
    </tr>
    `;

    data.rows.forEach(r => {
        html += `
        <tr>
            <td>${r.activity}</td>
            <td>${r.amount1}</td>
            <td>${r.amount2}</td>
            <td style="color:${r.status === 'Matched' ? 'green' : 'red'}">
                ${r.status}
            </td>
        </tr>
        `;
    });

    html += "</table>";

    document.getElementById("result").innerHTML = html;
}