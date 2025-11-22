
const express = require("express");
const multer = require("multer");
const axios = require("axios");
const path = require("path");
const FormData = require("form-data");   // ⬅️ IMPORTANT: you were using FormData but not importing it

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// View engine + views folder
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Serve static files (CSS) from /public
app.use(express.static(path.join(__dirname, "public")));

app.use(express.urlencoded({ extended: true }));

// Home page (upload images)
app.get("/", (req, res) => {
    res.render("index");
});

// Handle image upload
app.post("/generate", upload.array("images"), async (req, res) => {
    try {
        const style = req.body.style || "Wholesome Diary";

        const formData = new FormData();
        req.files.forEach(file => {
            formData.append("files", file.buffer, {
                filename: file.originalname,
                contentType: file.mimetype
            });
        });
        formData.append("style", style);

        // Call FastAPI backend
        const response = await axios.post(
            "http://127.0.0.1:8000/generate-story",
            formData,
            { headers: formData.getHeaders() }
        );

        const storyData = response.data;

        res.render("story", { story: storyData });

    } catch (err) {
        console.error("Error in /generate:", err.message);
        res.send("Error generating story");
    }
});

app.listen(3000, () => {
    console.log("Frontend running at http://localhost:3000");
});
