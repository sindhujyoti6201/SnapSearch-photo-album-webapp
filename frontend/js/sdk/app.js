// const apigClient = apigClientFactory.newClient();

// function uploadPhoto() {
//     console.log("===================UPLOADING========================");
//     const fileInput = document.getElementById('photoFile');
//     const labelsInput = document.getElementById('customLabels');
//     const file = fileInput.files[0];
//     const customLabels = labelsInput.value;

//     if (!file) {
//         alert("Please select a file to upload.");
//         return;
//     }

//     const reader = new FileReader();
//     reader.onload = function (event) {
//         const binaryData = event.target.result;
//         const params = {
//             filename: file.name
//         };

//         const additionalParams = {
//             headers: {
//                 'Content-Type': file.type,
//                 'x-amz-meta-customLabels': customLabels
//             }
//         };

//         apigClient.uploadPut(params, binaryData, additionalParams)
//             .then(result => {
//                 alert("Photo uploaded successfully!");
//             })
//             .catch(error => {
//                 console.error("Upload failed: ", error);
//                 alert("Upload failed.");
//             });
//     };
//     reader.readAsArrayBuffer(file);
// }

// function searchPhotos() {
//     console.log("===================SEARCHING========================");
//     const query = document.getElementById('searchQuery').value;
//     const params = {
//         q: query
//     };

//     apigClient.searchGet(params, {}, {})
//         .then(response => {
//             const results = document.getElementById('results');
//             results.innerHTML = '';
//             const photos = response.data.results || [];
//             photos.forEach(url => {
//                 const img = document.createElement('img');
//                 img.src = url;
//                 results.appendChild(img);
//             });
//         })
//         .catch(error => {
//             console.error("Search failed: ", error);
//             alert("Search failed.");
//         });
// }



const apigClient = apigClientFactory.newClient();

function uploadPhoto() {
    console.log("=================== UPLOADING ====================");
    const fileInput = document.getElementById('photoFile');
    const labelsInput = document.getElementById('customLabels');
    const file = fileInput.files[0];
    const customLabels = labelsInput.value;

    if (!file) {
        alert("Please select a file to upload.");
        return;
    }

    const reader = new FileReader();
    reader.onload = function (event) {
        const binaryData = event.target.result;

        const params = {
            filename: file.name,
            'x-amz-meta-customLabels': customLabels || ''
        };

        const additionalParams = {
            headers: {
                'Content-Type': file.type
            }
        };

        apigClient.uploadPut(params, binaryData, additionalParams)
            .then(result => {
                console.log("✅ Upload successful:", result);
                alert("Photo uploaded successfully!");
            })
            .catch(error => {
                console.error("❌ Upload failed:", error);
                alert("Upload failed.");
            });
    };
    reader.readAsArrayBuffer(file);
}

function searchPhotos() {
    console.log("=================== SEARCHING ====================");
    const query = document.getElementById('searchQuery').value.trim();

    if (!query) {
        alert("Please enter a search query.");
        return;
    }

    const params = { q: query };

    apigClient.searchGet(params, {}, {})
        .then(response => {
            console.log("✅ Search response:", response);

            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';

            const photoData = response.data;

            if (photoData.image_data_base64) {
                const img = document.createElement('img');
                img.src = `data:${photoData.content_type};base64,${photoData.image_data_base64}`;
                img.alt = photoData.filename;
                resultsDiv.appendChild(img);
            } else if (photoData.message) {
                resultsDiv.innerHTML = `<p>${photoData.message}</p>`;
            } else {
                resultsDiv.innerHTML = "<p>No image found.</p>";
            }
        })
        .catch(error => {
            console.error("❌ Search failed:", error);
            alert("Search failed.");
        });
}
