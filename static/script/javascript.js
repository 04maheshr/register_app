let filesArray = [];
function addFileToList() {
    const fileInput = document.getElementById("pdfFiles");
    const files = fileInput.files;
    const fileList = document.getElementById("form-group");
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        filesArray.push(file);
        let li = document.createElement("li");
        li.textContent = file.name;
        let deleteButton = document.createElement("button");
        deleteButton.textContent = "delete";
        deleteButton.onclick = () => {
            filesArray = filesArray.filter(f => f.name !== file.name);
            li.remove();
        };

        li.appendChild(deleteButton);
        fileList.appendChild(li);
    }
    fileInput.value = "";
}
async function submitForm(event) {
    event.preventDefault();

    const textarea = document.getElementById("regNumbers");
    let regNumbers = textarea.value;
    let regNumbersArray = regNumbers.split(',').map(number => number.trim());
    let formdata = new FormData();
    formdata.append("regNumbers", JSON.stringify(regNumbersArray));
    for (let i = 0; i < filesArray.length; i++) {
        formdata.append("pdfFiles", filesArray[i]);
        console.log(filesArray[i])
    }
    for (let pair of formdata.entries()) {
        console.log(pair[0] + ':', pair[1]);
    }
    try {
        let response = await fetch("/upload", {
            method: 'POST',
            body: formdata
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        if (!data.success) {
            console.error('Error:', data.message);
            alert('Failed to upload files: ' + data.message);
        } else {
            console.log('Files:', data.files);
            alert('Files uploaded successfully.');
            const downloadLink = document.createElement('a');
            downloadLink.href = data.download_url;
            downloadLink.textContent = 'Download Results';
            downloadLink.style.display = 'block';
            downloadLink.setAttribute('download', 'results.xlsx')
            document.body.appendChild(downloadLink);
        }
    } catch (error) {
        console.error('Fetch error:', error);
        alert('Error uploading files.');
    }
}
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("uploadForm").addEventListener("submit", submitForm);
    document.getElementById("addFileButton").addEventListener("click", addFileToList);
});



