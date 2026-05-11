function uploadFile() {
    let fileInput = document.querySelector("input[type='file']");
    
    if (!fileInput.files.length) {
        alert("Please select a file!");
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);

        // ✅ Fill error table
        let table = document.querySelector("tbody");
        table.innerHTML = "";

		data.errors.forEach(item => {
			let row = `<tr>
				<td>${item.error}</td>
				<td>${item.message}</td>
				<td>${item.suggestions.join(", ")}</td>
				<td>${item.sentence}</td>
			</tr>`;
			table.innerHTML += row;
		});

        // ✅ Show corrected text
        let output = document.getElementById("correctedText");
        if (output) {
            output.innerText = data.corrected;
        }
    })
    .catch(err => {
        console.error("Error:", err);
    });
}