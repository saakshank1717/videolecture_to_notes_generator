const videoForm = document.getElementById("videoForm");
const summaryText = document.getElementById("summaryText");
const downloadLink = document.getElementById("downloadLink");
const spinner = document.getElementById("spinner");
const outputCard = document.getElementById("outputCard");

videoForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    summaryText.textContent = "";
    spinner.style.display = "block";
    downloadLink.style.display = "none";
    outputCard.style.display = "none";

    const formData = new FormData(videoForm);

    try {
        const response = await fetch("/upload_video", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        spinner.style.display = "none";
        outputCard.style.display = "block";

        if (data.error) {
            summaryText.textContent = data.error;
            return;
        }

        summaryText.textContent = data.notes;
        downloadLink.href = `/download_pdf/${data.pdf_file.split("/").pop()}`;
        downloadLink.style.display = "inline-block";

    } catch (err) {
        spinner.style.display = "none";
        summaryText.textContent = "⚠️ Error processing video.";
        console.error(err);
    }
});
