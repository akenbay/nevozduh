const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to parse JSON
app.use(express.json());
app.use(express.static('public'));

// JSON database file
const DB_FILE = 'database.json';

// Initialize database if it doesn't exist
if (!fs.existsSync(DB_FILE)) {
    fs.writeFileSync(DB_FILE, JSON.stringify({ users: [] }, null, 2));
}

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

// Helper functions for database
function readDatabase() {
    const data = fs.readFileSync(DB_FILE, 'utf8');
    return JSON.parse(data);
}

function writeDatabase(data) {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

// API endpoint to register a user
app.post('/api/register', (req, res) => {
    const { username, telegramId } = req.body;
    const db = readDatabase();
    
    // Check if user already exists
    if (db.users.some(user => user.telegramId === telegramId)) {
        return res.status(400).json({ error: 'User already registered' });
    }
    
    // Add new user
    db.users.push({
        username,
        telegramId,
        registeredAt: new Date().toISOString()
    });
    
    writeDatabase(db);
    res.json({ success: true });
});

// API endpoint to get all registrations
app.get('/api/registrations', (req, res) => {
    const db = readDatabase();
    res.json(db.users);
});