from flask import Flask, render_template, request, jsonify
from rules import decide

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/decide")
def api_decide():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", ""))
    result = decide(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
