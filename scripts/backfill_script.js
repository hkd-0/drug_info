function backfillDatabaseIDs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Helper function to backfill specific sheets
  function fillSheet(sheetName, idPrefix, idHeaderName) {
    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) return;

    var range = sheet.getDataRange();
    var values = range.getValues();
    var headers = values[0];

    // Find exactly which columns contain our targets
    var snoCol = headers.indexOf("S.No.");
    var idCol = headers.indexOf(idHeaderName);

    if (snoCol === -1 || idCol === -1) return; // Skip if headers are missing

    // Loop through every row beneath the header
    for (var i = 1; i < values.length; i++) {
      var expectedSno = i; // Row 2 becomes S.No 1, Row 3 becomes 2, etc.
      
      // If S.No. is blank, fill it
      if (!values[i][snoCol] || values[i][snoCol] === "") {
        values[i][snoCol] = expectedSno;
      }
      
      // If the ID is blank, generate it (e.g., PROD-0001)
      if (!values[i][idCol] || values[i][idCol] === "") {
        values[i][idCol] = idPrefix + String(expectedSno).padStart(4, '0');
      }
    }
    
    // Write all changes back to the sheet in one massive, instant batch
    range.setValues(values);
  }

  // Execute for both tables
  fillSheet("drug_molecule", "M-", "Molecule_ID");
  fillSheet("medicinal_product", "PROD-", "Product_ID");
}