const express = require("express");
const app = express();
const { Client } = require("pg");

const client = new Client({
  host: "db",
  user: "postgres",
  password: "postgres",
  database: "postgres",
});

app.get("/", async (req, res) => {
  try {
    await client.connect();
    const result = await client.query("SELECT NOW()");
    await client.end();
    res.send("Conectado a Postgres dentro de Docker 🐳 Hora: " + result.rows[0].now);
  } catch (err) {
    res.send("Error conectando a Postgres: " + err);
  }
});

app.listen(3000, () => {
  console.log("App corriendo en puerto 3000");
});

