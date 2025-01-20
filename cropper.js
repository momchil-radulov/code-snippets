<input type="file" id="fileInput" name="files[]" accept="image/*" required>
// Зареждане на изображението
imageInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) {
        $('#preview').show();
        // Създаване на URL от файла
        const fileURL = URL.createObjectURL(file);
        
        // Актуализиране на източника на изображението
        preview.src = fileURL;

        // Ако вече има cropper, унищожаваме го
        if (cropper) cropper.destroy();

        // Създаване на нов Cropper
        cropper = new Cropper(preview, {
            viewMode: 2,
        });

        // Освобождаване на URL-а, когато вече не е необходим
        preview.onload = () => {
            URL.revokeObjectURL(fileURL);
        };
    }
});
