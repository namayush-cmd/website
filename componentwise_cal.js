document.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", calculateAll);
});

function getVal(id) {
    return parseFloat(document.getElementById(id)?.value) || 0;
}

function setVal(id, val) {
    document.getElementById(id).value = val.toFixed(2);
}

function calculateAll() {

    // ===== ROW TOTAL (example row1) =====
    let t1 = getVal("c1") + getVal("c2") + getVal("s1") + getVal("s2");
    let t2 = getVal("c3") + getVal("c4") + getVal("s3") + getVal("s4");

    setVal("t1", t1);
    setVal("t2", t2);

    // ===== ROW 2 =====
    let t11 = getVal("c11") + getVal("c12") + getVal("s11") + getVal("s12");
    let t12 = getVal("c13") + getVal("c14") + getVal("s13") + getVal("s14");

    setVal("t11", t11);
    setVal("t12", t12);

    // ===== ROW 3 =====
    let t21 = getVal("c21") + getVal("c22") + getVal("s21") + getVal("s22");
    let t22 = getVal("c23") + getVal("c24") + getVal("s23") + getVal("s24");

    setVal("t21", t21);
    setVal("t22", t22);
	
	    // ===== ROW 4 =====
    let t31 = getVal("c31") + getVal("c32") + getVal("s31") + getVal("s32");
    let t32 = getVal("c33") + getVal("c34") + getVal("s33") + getVal("s34");

    setVal("t31", t31);
    setVal("t32", t32);
	
	    // ===== ROW 5 =====
    let t41 = getVal("c41") + getVal("c42") + getVal("s41") + getVal("s42");
    let t42 = getVal("c43") + getVal("c44") + getVal("s43") + getVal("s44");

    setVal("t41", t41);
    setVal("t42", t42);
	
	    // ===== ROW 6 =====
    let t51 = getVal("c51") + getVal("c52") + getVal("s51") + getVal("s52");
    let t52 = getVal("c53") + getVal("c54") + getVal("s53") + getVal("s54");

    setVal("t51", t51);
    setVal("t52", t52);
	
    // ===== COLUMN TOTAL =====

    setVal("ct1", getVal("c1") + getVal("c11")+ getVal("c21")+ getVal("c31")+ getVal("c41")+ getVal("c51"));
    setVal("ct2", getVal("c2") + getVal("c12")+ getVal("c22")+ getVal("c32")+ getVal("c42")+ getVal("c52"));
    setVal("ct3", getVal("c3") + getVal("c13")+ getVal("c23")+ getVal("c33")+ getVal("c43")+ getVal("c53"));
    setVal("ct4", getVal("c4") + getVal("c14")+ getVal("c24")+ getVal("c34")+ getVal("c44")+ getVal("c54"));

    setVal("ct5", getVal("s1") + getVal("s11")+ getVal("s21")+ getVal("s31")+ getVal("s41")+ getVal("s51"));
    setVal("ct6", getVal("s2") + getVal("s12")+ getVal("s22")+ getVal("s32")+ getVal("s42")+ getVal("s52"));
    setVal("ct7", getVal("s3") + getVal("s13")+ getVal("s23")+ getVal("s33")+ getVal("s43")+ getVal("s53"));
    setVal("ct8", getVal("s4") + getVal("s14")+ getVal("s24")+ getVal("s34")+ getVal("s44")+ getVal("s54"));

// ===== FINAL TOTAL (CORRECT) =====

// Utilization Total (Recurring + Non-Recurring)
let totalUtil =
    getVal("ct1") + getVal("ct2") +
    getVal("ct5") + getVal("ct6");

// Refund Total (Recurring + Non-Recurring)
let totalRefund =
    getVal("ct3") + getVal("ct4") +
    getVal("ct7") + getVal("ct8");

setVal("ct9", totalUtil);
setVal("ct10", totalRefund);
}