function mapToBudgetTable() {

    // ===== UTILIZATION (CORRECT SOURCE) =====
    let cRec = getVal("ct1");
    let cNonRec = getVal("ct2");

    let sRec = getVal("ct5");
    let sNonRec = getVal("ct6");

    // ===== REFUND =====
    let cRefRec = getVal("ct3");
    let cRefNonRec = getVal("ct4");

    let sRefRec = getVal("ct7");
    let sRefNonRec = getVal("ct8");

    // ===== TOTAL =====
    let totalRec = cRec + sRec;
    let totalNonRec = cNonRec + sNonRec;

    let totalRefRec = cRefRec + sRefRec;
    let totalRefNonRec = cRefNonRec + sRefNonRec;

    // ===== MAP TO BUDGET TABLE =====

    // Recurring
    setVal("b_c_util_r", cRec);
    setVal("b_s_util_r", sRec);
    setVal("b_t_util_r", totalRec);

    setVal("b_c_ref_r", cRefRec);
    setVal("b_s_ref_r", sRefRec);
    setVal("b_t_ref_r", totalRefRec);

    // Non-Recurring
    setVal("b_c_util_nr", cNonRec);
    setVal("b_s_util_nr", sNonRec);
    setVal("b_t_util_nr", totalNonRec);

    setVal("b_c_ref_nr", cRefNonRec);
    setVal("b_s_ref_nr", sRefNonRec);
    setVal("b_t_ref_nr", totalRefNonRec);
}
	
	