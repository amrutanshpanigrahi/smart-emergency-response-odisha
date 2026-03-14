from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    print("==============================================")
    print("  IERN – Intelligent Emergency Response Network")
    print("  Odisha | Python + MySQL + ML + AI")
    print("==============================================")
    print("")
    print("  Patient app   →  http://localhost:5000/")
    print("  Driver tablet →  http://localhost:5000/driver")
    print("  Hospital dash →  http://localhost:5000/hospital")
    print("  Zone map      →  http://localhost:5000/zone-map")
    print("")
    print("  Starting server...")
    print("")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)